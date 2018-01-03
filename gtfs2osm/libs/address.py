import re

# Patterns for re
PATTERN_CITY = re.compile('\s?[XVI]{1,5}[.:,]{0,3}\s*$')
PATTERN_JS_2 = re.compile('\s*;\s*$')
PATTERN_HOUSENUMBER = re.compile('[0-9]{1,3}(\/[A-z]{1}|\-[0-9]{1,3}|)', re.IGNORECASE)
PATTERN_STREET = re.compile(
    '\s*.*\s*(útgyűrű|útfél|sétány|lejtő|liget|aluljáró|lejtó|park|ltp\.|ltp|sarok|szél|sor|körönd|köz|tér|tere|utca|körút|lakótelep|krt\.|krt|út|rét|sgt.|u\.|u){1}',
    re.UNICODE | re.IGNORECASE)
#PATTERN_CONSCRIPTIONNUMBER = re.compile('\s*(hrsz[.:]{0,2}){0,1}\s*[0-9]{4,5}(\/[0-9]{1,3}){0,1}[.]{0,1}\s*(hrsz[.]{0,1}){0,1}', re.IGNORECASE)
PATTERN_CONSCRIPTIONNUMBER = re.compile('(\s*[0-9]{2,5}(\/[0-9]{1,3}){0,1}[.]{0,1}\s*hrsz[s.]{0,1}|hrsz[.:]{0,2}\s*[0-9]{2,5}(\/[0-9]{1,3}){0,1}[.]{0,1})', re.IGNORECASE)
PATTERN_CONSCRIPTIONNUMBER_NUMBER = re.compile('[0-9]{2,5}(\/[0-9]{1,3}){0,1}', re.IGNORECASE)


def clean_javascript_variable(clearable, removable):
    """Remove javascript variable notation from the selected JSON variable.

    :param clearable: This is the text with Javascript text
    :param removable: The name of Javascript variable
    :return: Javascript clean text/JSON file
    """
    # Match on start
    PATTERN_JS = re.compile('^\s*var\s*{}\s*=\s*'.format(removable))
    data = re.sub(PATTERN_JS, '', clearable)
    # Match on end
    return re.sub(PATTERN_JS_2, '', data)


def extract_street_housenumber(clearable):
    '''Try to separate street and house number from a Hungarian style address string

    :param clearable: An input string with Hungarian style address string
    return: Separated street and housenumber
    '''
    # Split and clean up house number
    housenumber = clearable.split('(')[0]
    housenumber = housenumber.split(' ')[-1]
    housenumber = housenumber.replace('.', '')
    housenumber = housenumber.replace('–', '-')
    housenumber = housenumber.lower()
    # Split and clean up street
    street = clearable.split('(')[0]
    street = street.rsplit(' ', 1)[0]
    street = street.replace(' u.', ' utca')
    street = street.replace(' krt.', ' körút')
    return street, housenumber


def extract_street_housenumber_better(clearable):
    '''Try to separate street and house number from a Hungarian style address string

    :param clearable: An input string with Hungarian style address string
    return: Separated street and housenumber
    '''
    # Split and clean up street
    data = clearable.split('(')[0]
    cn_match = PATTERN_CONSCRIPTIONNUMBER.search(data)
    if cn_match is not None:
        conscriptionnumber = cn_match.group(0)
        cnn_length = len(conscriptionnumber)
        print(conscriptionnumber)
        cnn_match = PATTERN_CONSCRIPTIONNUMBER_NUMBER.search(conscriptionnumber)
        conscriptionnumber = cnn_match.group(0)
        print('LUCKYYYYYYYYYYY {}'.format(conscriptionnumber))
    else:
        conscriptionnumber = None
        cnn_length = None
    # Try to match street
    street_match = PATTERN_STREET.search(data)
    if street_match is None:
        print('jaj: {}'.format(clearable))
        street, housenumber = None, None
    else:
        # Normalize street
        street = street_match.group(0)
        street_length = len(street)
        street = street.replace('Szt.István', 'Szent István')
        street = street.replace('Kossuth L.', 'Kossuth Lajos')
        street = street.replace(' u.',   ' utca')
        street = street.replace('.u.',   ' utca')
        street = street.replace(' krt.', ' körút')
        street = street.replace(' ltp.', ' lakótelep')
        street = street.replace(' ltp',  ' lakótelep')
        street = street.replace(' sgt.', ' sugárút')

        # Search for house number
        if cnn_length is not None:
            hn_match = PATTERN_HOUSENUMBER.search(data[street_length:-cnn_length])
            print(data[street_length:-cnn_length])
        else:
            hn_match = PATTERN_HOUSENUMBER.search(data[street_length:])
        if hn_match is not None:
            # Split and clean up house number
            housenumber = hn_match.group(0)
            housenumber = housenumber.replace('.', '')
            housenumber = housenumber.replace('–', '-')
            housenumber = housenumber.lower()
        else:
            housenumber = None


    return street, housenumber, conscriptionnumber


def clean_city(clearable):
    '''Remove additional things from cityname

    :param clearable: Not clear cityname
    :return: Clear cityname
    '''
    city = re.sub(PATTERN_CITY, '', clearable)
    return city.strip()
