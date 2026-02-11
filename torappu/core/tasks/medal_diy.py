from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, cast

import UnityPy
from PIL import Image
from UnityPy.classes import MonoBehaviour, Sprite

from torappu.consts import STORAGE_DIR
from torappu.core.client import Client
from torappu.core.tasks.utils import get_gamedata, get_source, read_obj
from torappu.core.utils import run_sync
from torappu.models import Diff

from .base import BaseTask
from .medal_icon import BASE_DIR as MEDAL_ICON_DIR

BASE_DIR = STORAGE_DIR.joinpath("asset", "raw", "medal_diy")
BKG_DIR = BASE_DIR / "bkg"
TRIM_DIR = BASE_DIR / "trim"


@dataclass
class MedalPosition2DRect:
    x: float
    y: float


@dataclass
class MedalPosition:
    medalId: str
    pos: MedalPosition2DRect


class Task(BaseTask):
    priority: ClassVar[int] = 5

    def __init__(self, client: Client) -> None:
        super().__init__(client)

        self.ab_list = set()
        self.dict_medal_pos: dict[str, list[MedalPosition]] = {}
        self.dict_advanced: dict[str, str] = {}

    @run_sync
    def unpack_metadata(self, env: UnityPy.Environment, unpacking_source: list[str]):
        for obj in filter(lambda obj: obj.type.name == "MonoBehaviour", env.objects):
            source = get_source(obj)
            if source not in unpacking_source:
                continue

            if (behaviour := read_obj(MonoBehaviour, obj)) is None:
                continue

            script = behaviour.m_Script.deref_parse_as_object()
            if script.m_Name != "UIMedalGroupFrame":
                continue

            medal_group_id = cast("str", behaviour._groupId)  # type: ignore
            medal_pos_list = cast("list[MedalPosition]", behaviour._medalPosList)  # type: ignore

            self.dict_medal_pos[medal_group_id] = medal_pos_list

    def build_up(self, pos_list: list[MedalPosition], bg: Image.Image):
        result = bg.copy()
        for medal_pos in pos_list:
            medal_image_path = MEDAL_ICON_DIR / f"{medal_pos.medalId}.png"
            medal_image = Image.open(medal_image_path)

            # flip the y axis, pillow uses bottom-right as origin
            result.paste(
                medal_image,
                (
                    int(medal_pos.pos.x - medal_image.width / 2),
                    int(bg.height - medal_pos.pos.y - medal_image.height / 2),
                ),
                medal_image,
            )
        return result

    @run_sync
    def unpack_ab(self, env: UnityPy.Environment, resolved_paths: list[str]):
        for obj in filter(lambda obj: obj.type.name == "Sprite", env.objects):
            source = get_source(obj)
            if source not in resolved_paths:
                continue

            if (texture := read_obj(Sprite, obj)) is None:
                continue

            background_image = texture.image
            background_image.save(BKG_DIR / f"{texture.m_Name}.png")

            medal_pos_list = self.dict_medal_pos.get(texture.m_Name, None)
            if medal_pos_list is None:
                continue

            resized = background_image.resize((1374, 459))
            self.build_up(medal_pos_list, resized).save(
                BASE_DIR / f"{texture.m_Name}.png"
            )
            if any(medal.medalId in self.dict_advanced for medal in medal_pos_list):
                self.build_up(
                    [
                        MedalPosition(
                            (
                                self.dict_advanced[medal.medalId]
                                if medal.medalId in self.dict_advanced
                                else medal.medalId
                            ),
                            medal.pos,
                        )
                        for medal in medal_pos_list
                    ],
                    resized,
                ).save(TRIM_DIR / f"{texture.m_Name}.png")

    def check(self, diff_list: list[Diff]) -> bool:
        diff_set = {diff.path for diff in diff_list}

        has_medal_icon_diff = any(
            asset.startswith("arts/ui/medalicon") and bundle in diff_set
            for asset, bundle in self.client.asset_to_bundle.items()
        )

        self.ab_list = {
            bundle
            for asset, bundle in self.client.asset_to_bundle.items()
            if asset.startswith("arts/ui/medal/suitbkg")
            and (bundle in diff_set or has_medal_icon_diff)
        }

        return len(self.ab_list) > 0

    async def start(self):
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        BKG_DIR.mkdir(exist_ok=True)
        TRIM_DIR.mkdir(exist_ok=True)

        icon_data = get_gamedata(
            self.client.version.res_version, "excel/medal_table.json"
        )
        self.dict_advanced = {
            medal["medalId"]: medal["advancedMedal"]
            for medal in icon_data["medalList"]
            if medal.get("advancedMedal")
        }

        paths = await self.client.resolves(list(self.ab_list))
        resolved_paths = [path[1] for path in paths]
        resolved_filenames: list[str] = [
            Path(resolved_path).name for resolved_path in resolved_paths
        ]
        env = UnityPy.load(*self.client.anon_paths, *resolved_paths)

        metadata_paths = await self.client.resolves(
            list(
                {
                    bundle
                    for asset, bundle in self.client.asset_to_bundle.items()
                    if asset.startswith("ui/medal/[uc]groupframe")
                }
            )
        )
        resolved_metadata_paths = [path[1] for path in metadata_paths]
        resolved_metadata_filenames = [
            Path(resolved_path).name for resolved_path in resolved_metadata_paths
        ]
        metadata_env = UnityPy.load(*self.client.anon_paths, *resolved_metadata_paths)

        await self.unpack_metadata(metadata_env, resolved_metadata_filenames)
        await self.unpack_ab(env, resolved_filenames)
