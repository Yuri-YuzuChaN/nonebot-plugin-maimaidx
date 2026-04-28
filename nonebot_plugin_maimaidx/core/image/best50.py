from io import BytesIO
from pathlib import Path

from PIL import Image

from ...config import maiconfig
from ...constants import ACHIEVEMENT_LIST, BASE_RA_SPP
from ...resources import pic_dir, static
from ..clients.http import lxns_assets, qqlogo
from ..clients.lxns.models.collection import Collection
from ..database.qq import User
from ..merge.models import Best50, Player, Theme
from .base import ScoreBaseImage
from .tools import image_to_base64


class PlayerBest50(ScoreBaseImage):
    
    def __init__(
        self, 
        user: User,
        *, 
        player: Player, 
        best50: Best50, 
        icon: str | None = None
    ) -> None:
        self.service = user.service
        path = pic_dir / user.theme.value / "b50_bg.png"
        super().__init__(Image.open(path).convert("RGBA"), user.theme)
        if user.theme == Theme.CIRCLE:
            self.color = (249, 62, 172, 255)
        else:
            self.color = (124, 129, 255, 255)
        self.player = player
        self.best50 = best50
        self.qqid = user.user_id
        self.icon = icon

    def _get_base_ra(self, achievements: float) -> float:
        for i, threshold in enumerate(ACHIEVEMENT_LIST):
            if achievements < threshold:
                return BASE_RA_SPP[i]
        return BASE_RA_SPP[-1]
    
    def _calc_ds(self, rating: float, achievements: float) -> float:
        a = min(100.5, achievements) / 100
        return round(rating / (a * self._get_base_ra(achievements)), 1)

    def _findRaPic(self) -> str:
        """
        寻找指定的Rating图片
        
        Returns:
            `str` 返回图片名称
        """
        if self.player.rating < 1000:
            num = "01"
        elif self.player.rating < 2000:
            num = "02"
        elif self.player.rating < 4000:
            num = "03"
        elif self.player.rating < 7000:
            num = "04"
        elif self.player.rating < 10000:
            num = "05"
        elif self.player.rating < 12000:
            num = "06"
        elif self.player.rating < 13000:
            num = "07"
        elif self.player.rating < 14000:
            num = "08"
        elif self.player.rating < 14500:
            num = "09"
        elif self.player.rating < 15000:
            num = "10"
        else:
            num = "11"
        return f"UI_CMN_DXRating_{num}.png"
    
    async def _fetch_image(self, type: str, endpoint: str) -> BytesIO | Path:
        if not maiconfig.assets_online:
            return static / "mai" / type / f"UI_{type.capitalize()}_{endpoint}.png"
        return await lxns_assets(f"/{type}/{endpoint}")
    
    async def draw(self) -> BytesIO:
        """
        绘制Best50
        """
        logo = Image.open(pic_dir / "logo.png").resize((249, 120))
        name = Image.open(pic_dir / "Name.png")
        matchlevel = Image.open(
            pic_dir / f"UI_DNM_DaniPlate_{self.player.course_rank:02d}.png"
        ).resize((80, 32))
        classlevel  = Image.open(
            pic_dir / f"UI_FBR_Class_{self.player.class_rank:02d}.png"
        ).resize((90, 54))
        dx_rating = Image.open(pic_dir / self._findRaPic()).resize((186, 35))

        # logo
        self._im.alpha_composite(logo, (14, 60))
        
        # plate
        if not self.player.name_plate:
            plate_path = pic_dir / "UI_Plate_550101.png"
        elif isinstance(self.player.name_plate, Collection):
            plate_path = await self._fetch_image("plate", self.player.name_plate.id)
        else:
            plate_path = pic_dir / f"{self.player.name_plate}.png"
        self._im.alpha_composite(Image.open(plate_path).resize((800, 130)), (300, 60))
        
        # icon
        if self.player.icon:
            icon = await self._fetch_image("icon", self.player.icon.id) 
        elif self.qqid or self.icon:
            icon = BytesIO(await qqlogo(self.qqid, self.icon))
        else:
            icon = pic_dir / "UI_Icon_509506.png"
        self._im.alpha_composite(Image.open(icon).convert("RGBA").resize((120, 120)), (305, 65))

        # dx_rating
        self._im.alpha_composite(dx_rating, (435, 72))
        
        # rating
        for n, i in enumerate(f"{self.player.rating:05d}"):
            self._im.alpha_composite(
                Image.open(pic_dir / f"UI_NUM_Drating_{i}.png").resize((17, 20)), 
                (520 + 15 * n, 80)
            )
        self._im.alpha_composite(name, (435, 115))
        self._im.alpha_composite(matchlevel, (625, 120))
        self._im.alpha_composite(classlevel, (620, 60))
        
        # trophy
        if self.player.trophy:
            trophy_title = self.player.trophy.name
            rating = Image.open(
                pic_dir / f"UI_CMN_Shougou_{self.player.trophy.color.value}.png"
            ).resize((270, 27))
            font = self._sy
        else:
            trophy_title = (
                f"B35: {self.best50.sd_total} + B15: {self.best50.dx_total}"
                f" = {self.player.rating}"
            )
            rating = Image.open(pic_dir / "UI_CMN_Shougou_Rainbow.png").resize((270, 27))
            font = self._tb
        self._im.alpha_composite(rating, (435, 160))
        font.draw(
            570, 172, 14, 
            trophy_title, 
            (0, 0, 0, 255), "mm"
        )

        self._sy.draw(445, 135, 20, self.player.name, (0, 0, 0, 255), "lm")
        self._sy.draw(
            700, 1570, 22, 
            (
                "Designed by Yuri-YuzuChaN & BlueDeer233. "
                f"Data by {self.service.value}. Generated by {maiconfig.bot_name} BOT"
            ), 
            (249, 62, 172, 255), "mm", 5, (255, 255, 255, 255)
        )

        self.whiledraw(self.best50.sd, False)
        self.whiledraw(self.best50.dx, True)
        
        return image_to_base64(self._im)