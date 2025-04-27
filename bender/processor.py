import itertools

from bender.sound import Sound


class Processor:
    def process(self, sounds: list[Sound]) -> list[Sound]:
        raise NotImplementedError(
            f"process is not implemented in {self.__class__.__name__}"
        )


class SingleSoundProcessor(Processor):
    def process(self, sounds: list[Sound]) -> list[Sound]:
        return list(
            itertools.chain.from_iterable(self._process(sound) for sound in sounds)
        )

    def _process(self, sound: Sound) -> list[Sound]:
        raise NotImplementedError(
            f"_process is not implemented in {self.__class__.__name__}"
        )
