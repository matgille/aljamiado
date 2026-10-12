import copy
import json
import random
import sys

import lxml.etree as ET
import pandas as pd
import glob
import re
from collections import OrderedDict


input_dir = "data/xml"

def import_xml_to_dict():
	tei_namespace = {"tei": "http://www.tei-c.org/ns/1.0"}
	xml_files = glob.glob(f"{input_dir}/*.xml")
	sentences_pool = []
	for xml_file in xml_files[:10]:
		as_tree = ET.parse(xml_file)
		xslt_path = "to_text.xsl"
		xslt = ET.parse(xslt_path)
		transform = ET.XSLT(xslt)
		result = str(transform(as_tree))
		result = re.sub(r"\s+", " ", result)
		split_result = [''] + re.split(r"\.(\s[A-Z&⅋])", result)
		as_sentences = [
			split_result[i - 1] + split_result[i]
			for i in range(1, len(split_result) - 1, 2)
			if i + 1 < len(split_result)
		]
		sentences_pool.extend(as_sentences)
	return sentences_pool

def where_in_list(x, list_of_intervals):
	"""
	Find the index of the first interval in the list that is greater than x.
	:param x:
	:param list_of_intervals:
	:return:
	"""
	for idx, item in enumerate(list_of_intervals):
		try:
			item = float(item.replace(",", "."))
		except AttributeError:
			item = float(item)
		if x > float(item):
			continue
		else:
			return idx

def convert(sentence, table):
	for regexp_pattern, abjad_dict in table.items():
		if len(abjad_dict) == 1:
			sentence = re.sub(regexp_pattern, abjad_dict[1], sentence)
		else:
			dice_roll = random.randint(0, 100) / 100
			print(dice_roll)
			print(abjad_dict.keys())
			correct_idx = where_in_list(dice_roll, abjad_dict.keys())
			target_key = list(abjad_dict.keys())[correct_idx]
			sentence = re.sub(regexp_pattern, abjad_dict[target_key], sentence)

	return sentence


def compare_word_by_word(converted, target, orig):
	"""
	Compare source and target text word by word and highlight differences.

	Args:
		source (str): The converted text (Aljamiado)
		target (str): The reference text (Aljamiado)
		orig (str): The original Latin text

	Returns:
		dict: A dictionary containing comparison statistics
	"""
	# Split into words (handling Arabic script)
	converted_words = re.findall(r'\S+', converted)
	target_words = re.findall(r'\S+', target)
	orig_words = re.findall(r'\S+', orig)

	# Determine the maximum length for alignment
	max_len = max(len(converted_words), len(target_words), len(orig_words))

	print("\nWord-by-word comparison:")
	print("-" * 80)
	print(f"{'Original (Latin)':<25} | {'Target (Aljamiado)':<25} | {'Converted (Aljamiado)':<25} | {'Match'}")
	print("-" * 80)

	matches = 0
	for i in range(max_len):
		orig_word = orig_words[i] if i < len(orig_words) else "[MISSING]"
		conv_words = converted_words[i] if i < len(converted_words) else "[MISSING]"
		tgt_word = target_words[i] if i < len(target_words) else "[MISSING]"

		# Check if converted word matches reference
		match_status = "✓" if conv_words == tgt_word else "✗"
		if match_status == "✓":
			matches += 1

		print(f"{orig_word:<25}  {conv_words:<30}  {tgt_word:<25}  {match_status}")

	# Calculate statistics
	total_words = len(conv_words)
	accuracy = (matches / total_words) * 100 if total_words > 0 else 0

	print("\nStatistics:")
	print(f"Total words in original text: {len(orig_words)}")
	print(f"Total words in converted text: {total_words}")
	print(f"Total words in reference text: {len(target_words)}")
	print(f"Matching words: {matches}")
	print(f"Accuracy: {accuracy:.2f}%")

	return {
		'total_original_words': len(orig_words),
		'total_converted_words': total_words,
		'total_reference_words': len(target_words),
		'matching_words': matches,
		'accuracy': accuracy
	}


def treat_ramistes(sentence):


	i_semi_voyelles = re.compile("i([aeiou])")
	sentence = re.sub(i_semi_voyelles, r"j\1", sentence)


	u_semi_voyelles = re.compile(r"([aeuio])u([aeiou])")
	sentence = re.sub(u_semi_voyelles, r"\1v\2", sentence)

	return sentence

def main(example):
	# On importe d'abord la table de conversion
	imported_table_path = "documents/latin-to-aljamia.csv"
	table = pd.read_csv(imported_table_path, sep=",")
	print(table.columns)
	# Create a dictionary of lists to handle multiple values per key
	conversion_dict = OrderedDict()
	for pattern, position, abjad, exclude, prob in zip(table['Regexp'],
														table['Position'],
														table['Abjad'],
														table['exclude'],
														table['Probs']):
		pattern = pattern.strip()
		if exclude == "TRUE":
			continue
		if position == "initiale":
			abjad = " " + abjad
		if pd.isna(prob):
			prob = 1
		try:
			sum_probs = sum(float(key) for key in conversion_dict[pattern].keys())
			conversion_dict[pattern] = {**conversion_dict[pattern], **{sum_probs + float(prob): abjad}}
		except KeyError as e:
			conversion_dict[pattern] = {prob: abjad}

	for orig, realizations in conversion_dict.items():
		all_probs = realizations.keys()
		assert all(item <= 1 for item in all_probs), f"Probabilities must be between 0 and 1: {orig} {realizations}"
	# Convert defaultdict to regular dict for consistency
	conversion_dict = OrderedDict(conversion_dict)

	with open("/home/mgl/Documents/conversion_dict.json", "w") as output_test:
		output_test.write(json.dumps(dict(conversion_dict), indent=4))

	# Puis on s'occupe d'importer les données d'entrée
	if example:
		sentence = treat_ramistes(example)
		converted = convert(sentence.lower(), conversion_dict)
		print(converted)
	else:
		castilian_sentences = import_xml_to_dict()
		for sentence in castilian_sentences[1:2]:
			print(sentence)
			sentence = treat_ramistes(sentence)
			target = "لُش اَلْكَلْدَاشْ دَا اَلبَ اِ ءَالْجُئَازْ نُنْ بَّارَانْضَنْ اَنَانغُنُ اُمْنَا نِن اَنَانْغُنَ مَُلَارْ شُ ڧُوَاربُّ نِن نَانغُنَ كُشَ دَا شُ اَبَارْ شِ نُنْْ ڢُوَارَا كَارَلُشُ"
			print(sentence)
			converted = convert(sentence.lower(), conversion_dict)
			print(converted)
			compare_word_by_word(converted=converted, target=target, orig=sentence)



if __name__ == '__main__':
	if len(sys.argv) == 1:
		example = None
	else:
		example = sys.argv[1]
	main(example)