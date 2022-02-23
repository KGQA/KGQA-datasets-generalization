
import re

big_bracket_pattern = re.compile(r'[{](.*?)[}]', re.S)

angle_bracket_pattern = re.compile(r'[<](.*?)[>]', re.S)