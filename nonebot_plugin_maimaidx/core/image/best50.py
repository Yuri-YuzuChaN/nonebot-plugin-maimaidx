from bisect import bisect_right
from io import BytesIO
from pathlib import Path

from PIL import Image

from ...config import maiconfig
from ...resources import pic_dir, plate_version_dir, shougou_dir, static
from ..clients.http import online_assets, qqlogo
from ..database.qq import User
from ..merge.models import Best50, Player, ServiceName, Theme
from .base import ScoreBaseImage
from .tools import image_to_base64


class PlayerBest50(ScoreBaseImage):
    def __init__(
        self, user: User, *, player: Player, best50: Best50, is_username: bool = False
    ) -> None:
        if is_username:
            self.service = ServiceName.DIVINGFISH
            self.qqid = None
            self.theme = Theme.PRISM_PLUS
            path = pic_dir / self.theme.value / "b50.png"
        else:
            self.service = user.service
            self.qqid = user.qqid
            self.theme = user.theme
            path = pic_dir / self.theme.value / "lxb50.png"

        super().__init__(Image.open(path).convert("RGBA"), self.theme)
        if self.theme == Theme.CIRCLE:
            self.color = (249, 62, 172, 255)
        else:
            self.color = (124, 129, 255, 255)
        self.player = player
        self.best50 = best50

        self._logo = Image.open(pic_dir / self.theme.value / "logo.png").resize(
            (249, 120)
        )
        self._name = Image.open(pic_dir / "Name.png")
        _cr = self.player.course_rank
        _num = f"{_cr if _cr <= 10 else _cr + 1:02d}"
        self._matchlevel = Image.open(pic_dir / f"UI_DNM_DaniPlate_{_num}.png").resize(
            (80, 32)
        )
        self._classlevel = Image.open(
            pic_dir / f"UI_FBR_Class_{self.player.class_rank:02d}.png"
        ).resize((90, 54))

    def _find_ra_pic(self) -> str:
        rating = self.player.rating
        thresholds = [
            (1000, "01"),
            (2000, "02"),
            (4000, "03"),
            (7000, "04"),
            (10000, "05"),
            (12000, "06"),
            (13000, "07"),
            (14000, "08"),
            (14500, "09"),
            (15000, "10"),
        ]

        for limit, num in thresholds:
            if rating < limit:
                return f"UI_CMN_DXRating_{num}.png"

        if self.theme == Theme.CIRCLE:
            if rating < 16000:
                num = "11"
            elif rating < 17000:
                num = "12"
            else:
                num = "11"
        else:
            num = "11"

        return f"UI_CMN_DXRating_{num}.png"

    def _ra_pic_star(self) -> int:
        thresholds = [
            14000,
            14250,
            14500,
            14750,
            15000,
            15250,
            15500,
            15750,
            16000,
            16250,
            16500,
            16750,
        ]
        num_map = [1, 2, 1, 2, 1, 2, 3, 4, 1, 2, 3, 4]
        idx = bisect_right(thresholds, self.player.rating) - 1
        return f"UI_CMN_DXRating_Star_0{num_map[idx]}.png"

    async def _fetch_image(self, type: str, file_name: str) -> BytesIO | Path | None:
        file = f"UI_{type.capitalize()}_{file_name}.png"
        if not maiconfig.assets_online:
            return static / "mai" / type / file
        return await online_assets(f"/{type}/{file}")

    async def _draw_lxns(self):
        """绘制落雪B50"""
        # frame
        frame_path = await self._fetch_image("frame", self.player.frame.id)
        self._im.alpha_composite(Image.open(frame_path).resize((1400, 586)), (0, 0))

        # plate
        plate_path = await self._fetch_image("plate", self.player.name_plate.id)
        self._im.alpha_composite(Image.open(plate_path).resize((800, 130)), (25, 25))

        # icon
        icon = await self._fetch_image("icon", self.player.icon.id)
        self._im.alpha_composite(
            Image.open(icon).convert("RGBA").resize((120, 120)), (30, 30)
        )

        # trophy
        trophy_title = self.player.trophy.name
        shougou = Image.open(
            shougou_dir / f"UI_CMN_Shougou_{self.player.trophy.color.value}.png"
        ).resize((270, 27))
        self._im.alpha_composite(shougou, (160, 125))
        self._sy.draw(295, 137, 14, trophy_title, (0, 0, 0, 255), "mm")

        # rating
        dx_rating_size = (186, 35)
        dx_rating_star = None
        rating_num_x = 245
        rating_num_y = 45
        rating_num_gap = 15
        rating_num_size = (17, 20)

        if self.theme == Theme.CIRCLE and self.player.rating >= 14000:
            dx_rating_size = (170, 35)
            star_path = pic_dir / self.theme.value / self._ra_pic_star()
            dx_rating_star = Image.open(star_path).resize((21, 35))

            rating_num_x = 240
            rating_num_y = 47
            rating_num_gap = 13
            rating_num_size = (14, 17)

        ra_pic = pic_dir / self.theme.value / self._find_ra_pic()
        dx_rating = Image.open(ra_pic).resize(dx_rating_size)
        self._im.alpha_composite(dx_rating, (160, 37))

        if dx_rating_star is not None:
            self._im.alpha_composite(dx_rating_star, (315, 37))

        # rating
        for n, i in enumerate(f"{self.player.rating:05d}"):
            self._im.alpha_composite(
                Image.open(pic_dir / f"UI_NUM_Drating_{i}.png").resize(rating_num_size),
                (rating_num_x + rating_num_gap * n, rating_num_y),
            )

        # logo
        self._im.alpha_composite(self._logo, (1120, 450))
        self._im.alpha_composite(self._name, (160, 80))
        self._im.alpha_composite(self._matchlevel, (350, 85))
        self._im.alpha_composite(self._classlevel, (345, 25))

        # name
        self._sy.draw(170, 100, 20, self.player.name, (0, 0, 0, 255), "lm")
        self._sy.draw(
            700,
            1570,
            22,
            (
                "Designed by Yuri-YuzuChaN & BlueDeer233. "
                f"Data from {self.service.value}. Generated by {maiconfig.bot_name} BOT"
            ),
            self.color,
            "mm",
            5,
            (255, 255, 255, 255),
        )

        self.whiledraw(self.best50.sd, False, 650)
        self.whiledraw(self.best50.dx, True, 1500)

    async def _draw_diving_fish(self):
        """绘制水鱼B50"""
        # plate
        if not self.player.name_plate:
            plate_path = pic_dir / "UI_Plate_550101.png"
        else:
            plate_path = plate_version_dir / f"{self.player.name_plate}.png"
        self._im.alpha_composite(Image.open(plate_path).resize((800, 130)), (300, 60))

        # icon
        if self.qqid:
            icon = BytesIO(await qqlogo(self.qqid))
        else:
            icon = pic_dir / "UI_Icon_509506.png"
        self._im.alpha_composite(
            Image.open(icon).convert("RGBA").resize((120, 120)), (305, 65)
        )

        # trophy
        trophy_title = (
            f"B35: {self.best50.sd_total} + B15: {self.best50.dx_total}"
            f" = {self.player.rating}"
        )
        shougou = Image.open(shougou_dir / "UI_CMN_Shougou_Rainbow.png").resize(
            (270, 27)
        )
        self._im.alpha_composite(shougou, (435, 160))
        self._tb.draw(570, 172, 14, trophy_title, (0, 0, 0, 255), "mm")

        # rating
        dx_rating_size = (186, 35)
        dx_rating_star = None
        rating_num_x = 520
        rating_num_y = 80
        rating_num_gap = 15
        rating_num_size = (17, 20)

        if self.theme == Theme.CIRCLE and self.player.rating >= 14000:
            dx_rating_size = (170, 35)
            star_path = pic_dir / self.theme.value / self._ra_pic_star()
            dx_rating_star = Image.open(star_path).resize((21, 35))

            rating_num_x = 515
            rating_num_y = 82
            rating_num_gap = 13
            rating_num_size = (14, 17)

        ra_pic = pic_dir / self.theme.value / self._find_ra_pic()
        dx_rating = Image.open(ra_pic).resize(dx_rating_size)
        self._im.alpha_composite(dx_rating, (435, 72))

        if dx_rating_star is not None:
            self._im.alpha_composite(dx_rating_star, (590, 72))

        # rating
        for n, i in enumerate(f"{self.player.rating:05d}"):
            self._im.alpha_composite(
                Image.open(pic_dir / f"UI_NUM_Drating_{i}.png").resize(rating_num_size),
                (rating_num_x + rating_num_gap * n, rating_num_y),
            )

        # logo
        self._im.alpha_composite(self._logo, (14, 60))
        self._im.alpha_composite(self._name, (435, 115))
        self._im.alpha_composite(self._matchlevel, (625, 120))
        self._im.alpha_composite(self._classlevel, (620, 60))

        # name
        self._sy.draw(445, 135, 20, self.player.name, (0, 0, 0, 255), "lm")
        self._sy.draw(
            700,
            1570,
            22,
            (
                "Designed by Yuri-YuzuChaN & BlueDeer233. "
                f"Data by {self.service.value}. Generated by {maiconfig.bot_name} BOT"
            ),
            self.color,
            "mm",
            5,
            (255, 255, 255, 255),
        )

        self.whiledraw(self.best50.sd, False)
        self.whiledraw(self.best50.dx, True)

    async def draw(self) -> str:
        """
        绘制Best50

        Returns:
            `base64 str`
        """
        if self.service == ServiceName.DIVINGFISH:
            await self._draw_diving_fish()
        else:
            await self._draw_lxns()

        return image_to_base64(self._im)
