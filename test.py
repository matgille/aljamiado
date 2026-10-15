import sys
import unicodedata

import create_artificial_data as cad


def main():
	with open("tests/test_data.txt", "r") as input_file:
		examples = [item.replace("\n", "") for item in input_file.readlines()]

	for line in examples:
		splitted = line.split(";")
		orig = splitted.pop(0)
		target = [unicodedata.normalize('NFC', item.strip()) for item in splitted]
		converted = cad.treat_sentence(orig).strip()
		converted = unicodedata.normalize('NFC', converted)
		assert converted in target, \
			f"Erreur avec la phrase: \n{orig}\n        |{converted}|\nTarget: |{target}|"


if __name__ == '__main__':
	main()