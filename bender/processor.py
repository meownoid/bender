from bender.sound import Sound


class Processor:
    def process(self, sounds: list[Sound]) -> Sound:
        raise NotImplementedError(
            f"process is not implemented in {self.__class__.__name__}"
        )


class OneToOneProcessor(Processor):
    def process(self, sounds: list[Sound]) -> Sound:
        if not sounds:
            raise ValueError("No input sounds provided")
        if len(sounds) > 1:
            raise ValueError(
                "Multiple input sounds provided: this processor accepts a single sound"
            )
        return self._process(sounds[0])

    def _process(self, sound: Sound) -> Sound:
        raise NotImplementedError(
            f"_process is not implemented in {self.__class__.__name__}"
        )
