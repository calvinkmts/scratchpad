from typing import List


class Permutation:
    def permutate(self, s: List[str]) -> List[List[str]]:
        if len(s) == 0:
            return [[]]

        permutations = self.permutate(s[1:])

        temp_permutations = []

        for permutation in permutations:
            for i in range(len(permutation) + 1):
                new_permutation = permutation.copy()
                new_permutation.insert(i, s[0])
                temp_permutations.append(new_permutation)

        return temp_permutations

if __name__ == "__main__":
    permutation = Permutation()
    solution = permutation.permutate(s=["a", "b", "c"])
    print(len(solution))
    print(solution)
