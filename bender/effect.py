from bender.sound import Sound


class Effect:
    def process(self, sound: Sound) -> Sound:
        raise NotImplementedError(
            f"process is not implemented in {self.__class__.__name__}"
        )
