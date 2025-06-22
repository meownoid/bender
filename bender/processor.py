from bender.sound import Sound
from bender.utils import make_unique_output_path


class Processor:
    def process(self, sounds: list[Sound]) -> list[Sound]:
        raise NotImplementedError(
            f"process is not implemented in {self.__class__.__name__}"
        )


class OneToOneProcessor(Processor):
    def process(self, sounds: list[Sound]) -> list[Sound]:
        output = []
        for sound in sounds:
            result = self._process(sound)
            if result.filename is None or result.filename == sound.filename:
                filename = sound.filename if sound.filename is not None else "processed"
                result = result.with_filename(
                    make_unique_output_path(
                        filename,
                        ".wav",
                    )
                )
            output.append(result)

        return output

    def _process(self, sound: Sound) -> Sound:
        raise NotImplementedError(
            f"_process is not implemented in {self.__class__.__name__}"
        )


class OneToManyProcessor(Processor):
    def process(self, sounds: list[Sound]) -> list[Sound]:
        output = []
        for sound in sounds:
            results = self._process(sound)
            for i, result in enumerate(results):
                if result.filename is None or result.filename == sound.filename:
                    filename = (
                        sound.filename if sound.filename is not None else "processed"
                    )
                    result = result.with_filename(
                        make_unique_output_path(filename, ".wav", i)
                    )
                output.append(result)

        return output

    def _process(self, sound: Sound) -> list[Sound]:
        raise NotImplementedError(
            f"_process is not implemented in {self.__class__.__name__}"
        )
