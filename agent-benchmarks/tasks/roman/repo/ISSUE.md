# Bug report

`from_roman()` accepts garbage. It must convert valid Roman numerals 1-3999 (standard subtractive form, e.g. 'XIV'=14, 'MCMXCIV'=1994) and raise ValueError for invalid ones such as 'IIII', 'VX', 'IC', 'XM', 'VV', 'MMMM', '' and lowercase is allowed ('xiv'=14). Fix it.
