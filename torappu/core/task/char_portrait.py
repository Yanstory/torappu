from typing import ClassVar, cast

import UnityPy
from UnityPy.classes import Sprite, Texture2D

from torappu.consts import STORAGE_DIR
from torappu.core.utils import run_sync
from torappu.models import Diff

from .task import Task
from .utils import read_obj

BASE_PATH = STORAGE_DIR.joinpath("asset", "raw", "char_portrait")
ATLAS_DEST = BASE_PATH / "atlas"


class CharPortrait(Task):
    priority: ClassVar[int] = 3

    @run_sync
    def unpack(self, env: UnityPy.Environment):
        for obj in filter(lambda obj: obj.type.name == "Sprite", env.objects):
            if (sprite := read_obj(Sprite, obj)) is None:
                continue

            # unpack atlas
            texture = cast("Texture2D", sprite.m_RD.texture.read())
            if texture:
                texture.image.save(ATLAS_DEST / f"{sprite.m_Name}.png")

            sprite.image.save(BASE_PATH / f"{sprite.m_Name}.png")

    def check(self, diff_list: list[Diff]) -> bool:
        diff_set = {diff.path for diff in diff_list}
        self.ab_list = {
            bundle
            for asset, bundle in self.client.asset_to_bundle.items()
            if asset.startswith("arts/charportraits") and bundle in diff_set
        }

        return len(self.ab_list) > 0

    async def start(self):
        paths = await self.client.resolves(list(self.ab_list))
        BASE_PATH.mkdir(parents=True, exist_ok=True)
        ATLAS_DEST.mkdir(parents=True, exist_ok=True)

        env = UnityPy.load(*[path[1] for path in paths])
        self.load_anon(env)
        await self.unpack(env)
