# -*- coding: utf-8 -*- 

# converting strings with accents to similar ASCII characters
def accents2ascii(text):
    dic={ u"á": "a", u"é": "e", u"ě": "e", u"í": "i", u"ó": "o", u"ú": "u", u"ů": "u", u"ľ": "l", u"š": "s", u"č": "c", u"ť": "t", u"ž": "z", u"ý": "y", u"ď": "d", u"ň": "n", u"ô": "o",
            u"ŕ": "r", u"ř": "r", u"ĺ": "l", u"ä": "a", u"ü": "u", u"ö": "o", u"Á": "A", u"É": "E", u"Ě": "E", u"Í": "I", u"Ó": "O", u"Ú": "U", u"Ů": "U",u"Ľ": "L", u"Š": "S", u"Č": "C", u"Ť": "T",
            u"Ž": "Z", u"Ý": "Y", u"Ď": "D", u"Ň": "N", u"Ô": "O", u"Ŕ": "R", u"Ř": "R", u"Ĺ": "L", u"Ӓ": "A", u"Ö": "O", u"Ü": "U",  u"\xb4":""}
    for i, j in dic.iteritems():
        text = text.replace(i, j)
    return text

# alternative function
# def strip_accents(s):
#     import unicodedata
#     return ''.join(c for c in unicodedata.normalize('NFD', s)
#                   if unicodedata.category(c) != 'Mn')


def listFromString(string):
    letter=1
    spaceLessString=""
    for i in string:
        try:
            # treating double space
            if i==" " and string[letter]==" ":
                i=""
            # treating space + comma
            if i==" " and string[letter]==",":
                i=""
            # treating comma + spaces
            try:
                if i==" " and spaceLessString[-1]==",":
                    i=""
            except:
                pass
            letter+=1
            spaceLessString+=i
        except:
            pass

    splitValues = spaceLessString.split(",")
    return splitValues
    

def zeroAdder(i,positions):
    # function - adds zeros to convert all numbers to specific number of digits
    # i can be string and integer as well
    i_str = str(int(i))
    i_num = int(i)
    if i_num < 10:
        x = positions - 1
    elif i_num < 100:
        x = positions - 2
    elif i_num < 1000:
        x = positions - 3
    else:
        x = positions - 4
    sheet_num = x*'0' + i_str
    return sheet_num