import os


class SupportFunctions:
    def __init__(self) -> None:
        pass


    @classmethod
    def get_next_result_folder(cls, base_dir):
        if not os.path.exists(base_dir):
            return "1"

        numbers = []
        for name in os.listdir(base_dir):
            path = os.path.join(base_dir, name)
            if os.path.isdir(path) and name.isdigit():
                numbers.append(int(name))

        return str((max(numbers) + 1)) if numbers else "1"

        


