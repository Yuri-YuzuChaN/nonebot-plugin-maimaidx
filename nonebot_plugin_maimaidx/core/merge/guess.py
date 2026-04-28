import json
import random

import numpy as np
from PIL import Image

from ...resources import guess_file
from ..image.tools import image_to_base64, song_chart
from ..service import mai
from ..tool import writefile
from .models.guess import *
from .models.song import Song


class Guess:
    
    _group: dict[int, GuessDefaultData | GuessPicData] = {}
    switch: GuessSwitch
    hot_music_ids: list[int] = []

    def __init__(self) -> None:
        """猜歌类"""
        if not guess_file.exists():
            self.switch = GuessSwitch()
        else:
            self.switch = GuessSwitch.model_validate(
                json.load(open(guess_file, 'r', encoding='utf-8'))
            )
    
    def guess(self):
        """初始化猜歌数据"""
        for song in mai.total_list.root:
            count = 0
            for diff in song.difficulties:
                if diff.stats:
                    count += diff.stats.cnt if diff.stats.cnt else 0
            if count > 10000:
                self.hot_music_ids.append(song.song_id)
        self.guess_data = list(filter(lambda x: x.song_id in self.hot_music_ids, mai.total_list.root))

    def start(self, gid: int):
        """开始猜歌"""
        self._group[gid] = self.guessData()

    def startpic(self, gid: int):
        """开始猜曲绘"""
        self._group[gid] = self.guesspicdata()
        
    def calculate_frequency_weights(self, image: Image.Image) -> np.ndarray:
        """
        计算图像的频率权重，用于在图像中选择裁剪区域
        
        Params:
            `image`: PIL.Image.Image, 输入图像
        Returns:
            `np.ndarray` 频率权重矩阵
        """
        gray_image = np.array(image.convert('L'))
        freq = np.fft.fft2(gray_image)
        freq_shift = np.fft.fftshift(freq)
        magnitude = np.abs(freq_shift)
        normalized_magnitude = magnitude / magnitude.max()
        weights = normalized_magnitude ** 2
        return weights

    def select_crop_region(
        self, 
        weights: np.ndarray, 
        crop_width: int, 
        crop_height: int, 
        top_p: int
    ) -> tuple[int, int]:
        h, w = weights.shape
        valid_regions = weights[:h - crop_height + 1, :w - crop_width + 1]
        flattened_weights = valid_regions.flatten()
        threshold = np.percentile(flattened_weights, top_p)
        valid_indices = np.where(flattened_weights >= threshold)[0]
        probabilities = flattened_weights[valid_indices]
        probabilities /= probabilities.sum()
        chosen_index = np.random.choice(valid_indices, p=probabilities)
        top_left_y = chosen_index // valid_regions.shape[1]
        top_left_x = chosen_index % valid_regions.shape[1]
        return top_left_x, top_left_y
    
    def pic(self, song: Song) -> Image.Image:
        """裁切曲绘"""
        im = Image.open(song_chart(song.id))
        w, h = im.size
        weights = self.calculate_frequency_weights(im)
        scale = random.uniform(0.15, 0.4)  # 裁剪尺寸范围 可在此修改
        w2, h2 = int(w * scale), int(h * scale)
        top_p = min(1.3 - np.power(scale, 0.4), 0.95) * 100
        x, y = self.select_crop_region(weights, w2, h2, top_p)
        im = im.crop((x, y, x + w2, y + h2))
        return im

    def guesspicdata(self) -> GuessPicData:
        """猜曲绘数据"""
        song = random.choice(self.guess_data)
        pic = self.pic(song)
        answer = mai.total_alias_list.by_id(song.song_id)[0].alias
        answer.append(song.song_id)
        return GuessPicData(song=song, img=image_to_base64(pic), answer=answer, end=False)

    def guessData(self) -> GuessDefaultData:
        """猜歌数据"""
        song = random.choice(self.guess_data)
        guess_options = random.sample([
            f"的 Expert 难度是 {song.difficulties[2].level}",
            f"的 Master 难度是 {song.difficulties[3].level}",
            f"的分类是 {song.genre}",
            f"的版本是 {song.version_str}",
            f"的艺术家是 {song.artist}",
            f"{'不' if song.type == 'SD' else ''}是 DX 谱面",
            f"{'没' if len(song.difficulties) == 4 else ''}有白谱",
            f"的 BPM 是 {song.bpm}"
        ], 6)
        answer = mai.total_alias_list.by_id(song.song_id)[0].alias
        answer.append(song.song_id)
        pic = self.pic(song)
        return GuessDefaultData(
            song=song, 
            img=image_to_base64(pic), 
            answer=answer, 
            end=False, 
            options=guess_options
        )

    def end(self, gid: int):
        """结束猜歌"""
        del self._group[gid]

    async def on(self, gid: int) -> str:
        """开启猜歌"""
        if gid not in self.switch.enable:
            self.switch.enable.append(gid)
        if gid in self.switch.disable:
            self.switch.disable.remove(gid)
        await writefile(guess_file, self.switch.model_dump())
        return '群猜歌功能已开启'

    async def off(self, gid: int) -> str:
        """关闭猜歌"""
        if gid not in self.switch.disable:
            self.switch.disable.append(gid)
        if gid in self.switch.enable:
            self.switch.enable.remove(gid)
        if gid in self._group:
            self.end(gid)
        await writefile(guess_file, self.switch.model_dump())
        return '群猜歌功能已关闭'


guess = Guess()