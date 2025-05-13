import csv
import json
import re

class MaximumForwardMatcher:
    def __init__(self, dictionary, zhdict):
        #self.dictionary = set(dictionary)  # 使用集合加速查找
        self.dictionary = dictionary
        self.zhdict = zhdict
        self.max_word_length = max(len(word) for word in dictionary)  # 最大单词长度

    def segment_zh(self, text):
        """对输入的文本进行分词"""
        index = 0
        words = []
        
        text_length = len(text)
        
        while index < text_length:
            match_found = False
            # 从当前位置尝试匹配最长的单词
            for size in range(self.max_word_length, 0, -1):
                if index + size > text_length:
                    continue
                word = text[index:index+size]
                if word in self.zhdict:
                    words.append(word)
                    index += size
                    match_found = True

                    break
            
            # 若没有匹配成功，将当前位置的字符作为单字切分
            if not match_found:
                words.append(text[index])
                index += 1

        return words

    
    def segment_chem_text(self, text):
        """对输入的文本进行分词"""
        index = 0
        words = []
        tags_chem = []
        tags_org = []
        tags_unorg = []

        text_length = len(text)
        
        while index < text_length:
            match_found = False
            # 从当前位置尝试匹配最长的单词
            for size in range(self.max_word_length, 0, -1):
                if index + size > text_length:
                    continue
                word = text[index:index+size]

                if word in self.dictionary:

                    val = self.dictionary[word]
                    tagcom = val[0]      #common
                    tagorgyusu = val[1]     #orgyusu
                    tagorg = val[2]         #org
                    tagunorgyusu = val[3]     #unorgyusu
                    tagunorg = val[4]         #unorg

                    isbiaodian = check_isbiaodian(text, index, len(word))
                    if (tagcom.startswith('c_biaodian') or tagcom.startswith('c_kuohao')) and isbiaodian:
                       isbiaodian=True
                    elif is_english_letter(text[index]) and check_isletter(text, index):
                        isletter = True
                    else:
                        words.append(word)
                        index += size
                        match_found = True
                        tags_chem.append('1')

                        if len(tagcom) > 0:
                            tags_org.append(tagcom)
                            tags_unorg.append(tagcom)
                            break

                        if len(tagorgyusu) > 0:
                            tags_org.append(tagorgyusu)
                        elif len(tagorg) > 0:
                            tags_org.append(tagorg)
                        else:
                            tags_org.append('0')
                        
                        if len(tagunorgyusu) > 0:
                            tags_unorg.append(tagunorgyusu)
                        elif len(tagunorg) > 0:
                            tags_unorg.append(tagunorg)
                        else:
                            tags_unorg.append('0')

                        break
                
            # 若没有匹配成功，将当前位置的字符作为单字切分
            if not match_found:
                words.append(text[index])
                index += 1

                tags_chem.append('0')
                tags_org.append('0')
                tags_unorg.append('0')

        unitarr = find_number_unit_sequences(words, 0, len(words)-1)
        wordarr = find_word_sequences(words, 0, len(words)-1)
        numarr = find_num_sequences(words, 0, len(words)-1)
        chemarr = is_chemical_formula(words, 0, len(words)-1)
        commarr = []
        commarr.extend(unitarr)
        commarr.extend(chemarr)
        commarr.extend(wordarr)
        commarr.extend(numarr)
        for unit in commarr:
            s = unit[0]
            e = unit[1]
            for i in range(s, e+1):
                tags_chem[i] = '0'
                tags_org[i] = '0'
                tags_unorg[i] = '0'

        return words, tags_chem, tags_org, tags_unorg

    def segment_chem_words(self, zhwords):
        """对输入的文本进行分词"""
        index = 0
        words = []
        tags_chem = []
        tags_org = []
        tags_unorg = []

        n = len(zhwords)
        
        while index < n:
            match_found = False
            # 从当前位置尝试匹配最长的单词
            for size in range(self.max_word_length, 0, -1):
                if index + size >= n:
                    continue
                word = ''.join(word for word in zhwords[index:index+size])
                #word = text[index:index+size]
                if word in self.dictionary:
                    words.append(word)
                    index += size
                    match_found = True

                    tags_chem.append('1')

                    val = self.dictionary[word]
                    tagcom = val[0]      #common
                    tagorgyusu = val[1]     #orgyusu
                    tagorg = val[2]         #org
                    tagunorgyusu = val[3]     #unorgyusu
                    tagunorg = val[4]         #unorg

                    if len(tagcom) > 0:
                        tags_org.append(tagcom)
                        tags_unorg.append(tagcom)
                        break

                    if len(tagorgyusu) > 0:
                        tags_org.append(tagorgyusu)
                    elif len(tagorg) > 0:
                        tags_org.append(tagorg)
                    else:
                        tags_org.append('0')
                    
                    if len(tagunorgyusu) > 0:
                        tags_unorg.append(tagunorgyusu)
                    elif len(tagunorg) > 0:
                        tags_unorg.append(tagunorg)
                    else:
                        tags_unorg.append('0')

                    break
            
            # 若没有匹配成功，将当前位置的字符作为单字切分
            if not match_found:
                words.append(zhwords[index])
                index += 1

                tags_chem.append('0')
                tags_org.append('0')
                tags_unorg.append('0')

        return words, tags_chem, tags_org, tags_unorg

def find_number_unit_sequences(words, start, end):
    units = {'mg','g', 'l','μl', 'ml','mol','mmol','克','升','毫升','摩尔','毫摩尔','%'}
    unitsre = '|'.join(u for u in units)
    #r'^\d+mg|^/mg'
    restr = r'^\d+([.]\d+)?(?:' + unitsre + ')$'
    sequences = []
    
    i = start
    while i <= end:
        num_unit_str = ''
        j = i
        ok = False
        while ((j <= end) and (j-i<15)):
            num_unit_str += words[j]
            ok = re.match(restr, num_unit_str)

            if ok is not None:
                break
            else:
                j += 1
        
        if j > i and ok is not None:
            sequences.append((i, j))
            i = j+1
        else:
            i += 1
            
    #assert len(sequences)<3
    print("========unit sequences=", sequences)
    return sequences

def find_word_sequences(words, start, end):
    sequences = []
    
    i = start
    while i <= end:
        j = i+20
        if j>end:
            j=end
        ok = False
        while j>=i:
            tmpstr = ''.join(w for w in words[i:j+1])
            if re.match("^[a-z0-9]+$", tmpstr) and len(tmpstr)>=3:
                ok = True
                break
            else:
                j -= 1
        
        if j > i and ok:
            sequences.append((i, j))
            i = j+1
        else:
            i += 1
            
    #assert len(sequences)<3
    print("========word sequences=", sequences)
    return sequences

def find_num_sequences(words, start, end):
    sequences = []
    
    i = start
    while i <= end:
        j = i+20
        if j>end:
            j=end
        ok = False
        while j>=i:
            tmpstr = ''.join(w for w in words[i:j+1])
            if re.match(r'^-?\d+(\.\d+)?$', tmpstr) and len(tmpstr)>=2:
                ok = True
                break
            else:
                j -= 1
        
        if j > i and ok:
            sequences.append((i, j))
            i = j+1
        else:
            i += 1
            
    #assert len(sequences)<3
    print("========word sequences=", )
    return sequences

def is_chemical_formula(words, start, end):
   
    schem='(he|li|be|cu|ne|na|mg|al|si|cl|ar|ca|sc|ti|cr|mn|fe|co|ni|zn|ga|ge|as|se|br|kr|rb|sr|zr|nb|mo|tc|ru|rh|pd|ag|cd|in|sn|sb|te|xe|cs|ba|la|ce|pr|nd|pm|sm|eu|gd|tb|dy|ho|er|tm|yb|lu|hf|ta|re|os|ir|pt|au|hg|tl|pb|bi|po|at|rn|fr|ra|ac|th|pa|np|pu|am|cm|bk|cf|es|fm|md|no|lr|rf|db|sg|bh|hs|mt|ds|rg|k|c|h|n|o|f|b|p|s|y|i|w|u|v)'
    jianhao = '(\-|‑|‐|‒|–)'
    unit = '(' + jianhao + '?' + schem + '+' + jianhao + '?(\d*)?)' 
    pattern = '(\(' + unit + '\)|' + unit + ')+'    
    regex = re.compile(pattern)

    #textinner = textinner.replace('‑', '-')
    #textinner = textinner.replace('‐', '-')
    #textinner = textinner.replace('‒', '-')
    #textinner = textinner.replace('–', '-')

    sequences = []
    arr = []
    
    i = start
    while i <= end:
        j = i+20
        if j>end:
            j=end
        ok = False
        while j>=i:
            tmpstr = ''.join(w for w in words[i:j+1])
            #-|‑|‐|‒|–
            s2 = re.sub(r'(-|‑|‐|‒|–)', '', tmpstr)
            res = regex.fullmatch(tmpstr)
            if res is not None and len(tmpstr)>2 and len(s2)>1:# 
                ok = True
                break
            else:
                j -= 1
        
        if j > i and ok:
            sequences.append((i, j))
            arr.append(tmpstr)
            i = j+1
        else:
            i += 1
            
    #assert len(sequences)<3
    print("========chemformula sequences=", sequences)
    print("========chemformula arr=", arr)
    return sequences

def read_anno_dict(file_path):
    term_dict = {}
    cnt = 1
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line.startswith("//"):
                continue
            if line: 
                term1, term2, term3 = line.split('=')
                term_dict[term3] = str(cnt)
                cnt += 1
    return term_dict

cate2id = read_anno_dict("./data/annotation/cate2id.txt")

def read_file_to_dict(file_path):
    term_dict = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line.startswith("//"):
                continue
            if line: 
                term1, term2 = line.split('\t', 1)
                term_dict[term1] = term2
    return term_dict
 
file_path = './data/org_word2cate.txt'
org_word2cate = read_file_to_dict(file_path)

def load_csv_to_dict(file_path):
    data_dict = {}
    
    with open(file_path, mode='r', encoding='utf-8-sig') as csvfile:
        csvreader = csv.DictReader(csvfile)
        #next(csvreader)
        for row in csvreader:
            # Extract the key and values from the row
            if not any(row):
                continue
            key = row['Column1']

            if not key or key.startswith('//'):
                continue
            value = (
                row['common'],
                row['orgyusu'],
                row['org'],
                row['unorgyusu'],
                row['unorg']
            )
            # Add to dictionary
            data_dict[key] = value
    
    return data_dict

def load_ik_dict():
    ik_dict = {}
    
    with open("./data/main2012.dic", mode='r', encoding='utf-8-sig') as file:
        for line in file:
            word = line.strip()  # 去除每行末尾的换行符和可能的空白
            ik_dict[word] = "ik"
    
    return ik_dict

def load_jieba_dict():
    jieba_dict = {}
    
    with open("./data/jiebadict.txt", mode='r', encoding='utf-8-sig') as file:
        for line in file:
            if line.startswith("//"):
                continue
            word = line.strip()  # 去除每行末尾的换行符和可能的空白
            arr = word.split(" ")
            if len(arr) != 3:
                continue

            jieba_dict[arr[0]] = arr[2]
    
    return jieba_dict

def load_terms_dict():
    termsdict = {}
    
    with open("./data/qidf.dat", mode='r', encoding='utf-8-sig') as file:
        for line in file:
            if line.startswith("//"):
                continue
            word = line.strip()  # 去除每行末尾的换行符和可能的空白
            arr = word.split("\t")
            if len(arr) != 3:
                continue
            idf = float(arr[2])
            termsdict[arr[0]] = idf
    
    return termsdict

#ikdict = load_ik_dict()
#jiebadict = load_jieba_dict()
cndict = load_terms_dict()

#dictionary = ["北京", "大学", "北京大学", "生活", "很", "美好"]
dictionary = load_csv_to_dict("./chemelem.csv")

matcher = MaximumForwardMatcher(dictionary, cndict)
 
def fullwidth_to_halfwidth(s):
    result = []
    for char in s:
        # 获取字符的 Unicode 编码
        code_point = ord(char)
        # 如果是全角标点符号（范围在 0xFF00 到 0xFF5E）
        if 0xFF01 <= code_point <= 0xFF5E:
            # 转换为半角标点符号
            result.append(chr(code_point - 0xFEE0))
        # 如果是全角空格（0x3000）
        elif code_point == 0x3000:
            result.append(chr(0x20))
        else:
            # 不是全角标点符号，直接添加
            result.append(char)
    return ''.join(result)

def find_all_indices(arr, target):
    indices = []  # 用于存储所有匹配元素的下标
    for index, element in enumerate(arr):  # 遍历列表并获取下标和元素
        if element == target:
            indices.append(index)  # 如果元素匹配，添加下标到结果列表
    return indices

def find_all_indices_for_elements(arr, target_elements):
    indices = []
    tags = []
    for index, element in enumerate(arr):
        if element in target_elements:
            indices.append(index)
            tags.append(element)
    return indices, tags

def tobeFiltered_seg_wuji(words, tags_unorg):
    cnt = 0
    yuansu_cnt = 0
    n = len(tags_unorg)
    for tag in tags_unorg:
        if (tag.startswith('cyuansu') or tag.startswith("cwuji_yusu_muti") or tag.startswith("cwuji_hhw") 
            or tag.startswith("cwuji_yusu_type") or tag.startswith("cwuji_yusu_houzhui_type")
             or tag.startswith("cwuji_yusu_jigen_duli")
              ):
            cnt = cnt + 1
            if tag.startswith('cyuansu'):
                yuansu_cnt = yuansu_cnt + 1

    if cnt == 0 : return True
    if yuansu_cnt == n : return True
    return False

def tobeFiltered_seg_youji(words, tags_org):
    cnt = 0
    n = len(tags_org)
    for tag in tags_org:
        if ((tag.startswith('cyuansu')) or tag.startswith("cyouji_yusu_muti") or tag.startswith("cyouji_hhw")
             or (tag.startswith("cyouji_yusu_jigen") and tag != "cyouji_yusu_jigen_wujisuan")
             or tag.startswith("cyouji_yusu_type")):
            cnt = cnt + 1

    if cnt == 0 : return True
    return False

def highlight_entity(words, resentity):
    #entity, start, len, taglist, type
    result = []
    i = 0
    n = len(words)
    
    while i < n:
        # 检查当前索引是否在任何一个段落的范围内
        in_segment = False
        #for start, end in resentity_wuji:
        for j in range(len(resentity)):
            tup = resentity[j]
            #print("i=",i,", tup=",tup)
            start = tup[1]
            end = start + tup[2] - 1
            tag = tup[4]
            if start <= i <= end:
                in_segment = True
                # 如果在段落开始处，添加左括号
                if i == start:
                    result.append('【')
                break
        
        # 添加当前单词
        result.append(words[i])

        # 如果在段落结束处，添加右括号
        if in_segment:
            if i == end:
                result.append('】/'+tag)

        i += 1
    
    # 将结果列表拼接成一个字符串
    return ' '.join(result)

def highlight_entity_text(text, resentity):
    #entity, start, len, taglist, type
    result = []
    i = 0
    n = len(text)
    
    while i < n:
        # 检查当前索引是否在任何一个段落的范围内
        in_segment = False
        #for start, end in resentity_wuji:
        for j in range(len(resentity)):
            tup = resentity[j]
            #print("i=",i,", tup=",tup)
            start = tup[1]
            end = start + tup[2] - 1
            tag = tup[4]
            if start <= i <= end:
                in_segment = True
                # 如果在段落开始处，添加左括号
                if i == start:
                    result.append('【')
                break
        
        # 添加当前单词
        result.append(text[i])

        # 如果在段落结束处，添加右括号
        if in_segment:
            if i == end:
                result.append('】/'+tag)

        i += 1
    
    # 将结果列表拼接成一个字符串
    return ' '.join(result)

def contains_chinese(s):
    pattern = re.compile(r'[\u4e00-\u9fff]')
    return pattern.search(s) is not None

def is_chinese(char):
    # 判断一个字符是否是中文
    return '\u4e00' <= char <= '\u9fff'

def isArabicDigit(ch):
    return ch >= '0' and ch <= '9'

def is_english_letter(char):
    return char>='a' and char<='z' and len(char) == 1

def check_isshuzi(text, pos):
    #如果是正常的数字，返回true
    ch = text[pos]
    if isArabicDigit(ch)==False:
        return False

    prev_char = text[pos - 1] if pos > 0 else ''
    next_char = text[pos + 1] if pos < len(text) - 1 else ''

    if is_chinese(prev_char) or is_chinese(next_char):
        return True
    else:
        return False
    
def check_isbiaodian(text, pos, wordlen):
    #如果是正常的标点，返回true
    start = pos
    end = pos+wordlen-1
    ch = text[start : end+1]
    
    prev_char = text[start - 1] if start > 0 else ''
    next_char = text[end + 1] if end < len(text) - 1 else ''
    
    if pos == 0:
        if is_chinese(next_char):
            return True
        else:
            return False
    
    if pos == len(text) - 1:
        if is_chinese(prev_char):
            return True
        else:
            return False

    if ch == ';' or ch == ':':
        if is_chinese(prev_char) or is_chinese(next_char):
            return True
        else:
            return False
    
    if ch == ',':
        if is_chinese(prev_char) or is_chinese(next_char):
            return True
        else:
            return False

    if ch == '.':
        if isArabicDigit(prev_char) and isArabicDigit(next_char):
            return False
        else:
            return True

    if ch == '\"' or ch == '\'' or ch == '\"\'':
        if is_english_letter(prev_char) or isArabicDigit(prev_char):
            return False
        else:
            return True

    if ch == '→':
        if isArabicDigit(prev_char) and isArabicDigit(next_char):
            return False
        else:
            return True

    if ch == '-' or ch == '‑':
        if is_chinese(prev_char) and is_chinese(next_char):
            return True
        else:
            return False

    
    if ch == '(':
        if is_chinese(next_char) and is_chinese(prev_char):
            return True
        else:
            return False
        
    if ch == ')':
        if is_chinese(next_char) and is_chinese(prev_char):
            return True
        else:
            return False

    return False

def check_isletter(text, pos):
    #如果是正常的字母，返回true
    ch = text[pos]
    
    prev_char = text[pos - 1] if pos > 0 else ''
    next_char = text[pos + 1] if pos < len(text) - 1 else ''
    
    if pos == 0:
        if is_chinese(next_char):
            return True
        else:
            return False
    
    if pos == len(text) - 1:
        if is_chinese(prev_char):
            return True
        else:
            return False

    if is_chinese(next_char):
        return True
    
    return False

def isnotleftedge(tags, words, wordpos):
    tag = tags[wordpos]
    if tag.startswith('cyuansu'):
        return False
    if wordpos > 0:
        minnum = min(3, wordpos)
        for i in range(1, minnum+1):
            word = ''.join(words[wordpos-i : wordpos+1])
            if word in cndict:   #ikdict:
                idf = cndict[word]
                if idf < 0.6:
                    return True
        return False
    
def isnotrightedge(tags, words, wordpos):
    tag = tags[wordpos]
    if tag.startswith('cyuansu'):
        return False
    if wordpos < len(words)-1:
        gap = len(words) - 1 - wordpos
        minnum = min(3, gap)
        for i in range(1, minnum+1):
            word = ''.join(words[wordpos : wordpos+i+1])
            if word in cndict:    #ikdict:
                idf = cndict[word]
                if idf < 0.6:
                    return True

        return False

fileres = open("./data/entityres.txt", 'w', encoding='utf-8')

def is_wuji_yhw(text, words, tags_chem, tags_org, tags_unorg, mask_word, start, end):
    #判断无机氧化物
    yang_cnt = 0
    other_yuansu_cnt = 0
    for i in range(start, end + 1):
        word = words[i]
        if word=='氧':
            yang_cnt += 1
    
    for i in range(start, end + 1):
        word = words[i]
        tag = tags_unorg[i]
        if word!='氧' and tag.startswith("cyuansu"):
            other_yuansu_cnt += 1

    if yang_cnt==1 and other_yuansu_cnt==1:
        return True
    else:
        return False

def is_wuji_jian(text, words, tags_chem, tags_org, tags_unorg, mask_word, start, end):
    #判断无机碱
    yuansu_cnt = 0    
    yusu_jian_cnt = 0
    hhw_cnt = 0
    for i in range(start, end + 1):
        word = words[i]
        tag = tags_unorg[i]
        if tag=='cwuji_yusu_jian':
            yusu_jian_cnt += 1
        if tag=='cwuji_hhw_jian':
            hhw_cnt += 1
        if tag.startswith("cyuansu"):
            yuansu_cnt += 1

    if hhw_cnt > 0:
        return True
    elif yusu_jian_cnt==1 and yuansu_cnt==1:
        return True
    else:
        return False

def is_wuji_yan(text, words, tags_chem, tags_org, tags_unorg, mask_word, start, end):
    #判断无机盐
    tag = tags_unorg[end]
    if tag == 'cwuji_yusu_jigen_yan' or tag == 'cwuji_yusu_type_yan' or tag=='cwuji_hhw_yan':
        return True

    if tag == 'cyuansu_jinshu':
        #word = ''.join(w for w in words[start:end+1])
        #if word.find("氟") >= 0:
        #    return False
        
        return True
    
    return False

def cate_wuji(text, words, tags_chem, tags_org, tags_unorg, mask_word, new_start, new_end):

    if new_end == new_start:
        t1 = tags_unorg[new_start]
        if t1.startswith("cyuansu_"):
            cate = "cwuji_danzhi"
            if t1.endswith("_jinshu"):
                cate = "cwuji_danzhi_jinshu"
            elif t1.endswith("_feijinshu"):
                cate = "cwuji_danzhi_feijinshu"
            elif t1.endswith("_xiyouqiti"):
                cate = "cwuji_danzhi_xiyouqiti"

            return cate
    
    if (new_end - new_start == 1):
        taglist_wuji_yuansu = ['cyuansu_jinshu', 'cyuansu_feijinshu', 'cyuansu_xiyouqiti']# ['cwuji_yusu_danzhiqiti', 'cwuji_yusu_danzhijinshu', 'cwuji_yusu_danzhifeijinshu']
        taglist_wuji_danzhi = ['cwuji_yusu_danzhiqiti', 'cwuji_yusu_danzhijinshu', 'cwuji_yusu_danzhisu']

        t1 = tags_unorg[new_start]
        t2 = tags_unorg[new_end]
        if (t1 in taglist_wuji_danzhi) and (t2 in taglist_wuji_yuansu): #金属钠
            cate = "cwuji_danzhi"
            if t2.endswith("_jinshu"):
                cate = "cwuji_danzhi_jinshu"
            elif t2.endswith("_feijinshu"):
                cate = "cwuji_danzhi_feijinshu"
            elif t2.endswith("_xiyouqiti"):
                cate = "cwuji_danzhi_xiyouqiti"
            return cate
        elif (t2 in taglist_wuji_danzhi) and (t1 in taglist_wuji_yuansu): #钠金属
            cate = "cwuji_danzhi"
            if t1.endswith("_jinshu"):
                cate = "cwuji_danzhi_jinshu"
            elif t1.endswith("_feijinshu"):
                cate = "cwuji_danzhi_feijinshu"
            elif t1.endswith("_xiyouqiti"):
                cate = "cwuji_danzhi_xiyouqiti"
            return cate

    tag = tags_unorg[new_end]
    word = words[new_end]

    if new_end == new_start and word in ['酸','碱','盐']:
        cate = 'cate'
        return cate
    
    cate = "cwuji_hhw_qita"

    is_yhw = is_wuji_yhw(text, words, tags_chem, tags_org, tags_unorg, mask_word, new_start, new_end)
    is_jian = is_wuji_jian(text, words, tags_chem, tags_org, tags_unorg, mask_word, new_start, new_end)
    is_yan = is_wuji_yan(text, words, tags_chem, tags_org, tags_unorg, mask_word, new_start, new_end)

    if tag.startswith('cwuji_yusu_houzhui_type'):
        cate = "cate" 
    elif is_yhw:
        cate = "cwuji_hhw_yhw"
    elif is_jian:
        cate = "cwuji_hhw_jian"
    elif is_yan:
        cate = "cwuji_hhw_yan"
    elif tag.startswith('cwuji_yusu_jigen'):
        cate = "cwuji_jigen"
    elif tag == 'cwuji_yusu_type_suan' or tag=='cwuji_hhw_suan':
        cate = "cwuji_hhw_suan"
    elif tag == 'cwuji_yusu_type_jian':
        cate = "cwuji_hhw_jian"
    elif tag == 'cwuji_yusu_type_suangan':
        cate = "cwuji_hhw_yhw"
    elif tag == 'cwuji_yusu_fenzi':
        cate = "cwuji_jibenlizi_fenzi"
    elif tag == 'cwuji_yusu_lizi':
        cate = "cwuji_jibenlizi_lizi"
    elif tag == 'cwuji_yusu_yuanzi':
        cate = "cwuji_jibenlizi_yuanzi"
    #elif tag == 'cyuansu_jinshu':
    #    cate = "cwuji_hhw_yan"
    #elif tag == 'cwuji_yusu_jigen_yan':
    #    cate = "cwuji_hhw_yan"
    #elif tag.startswith('cwuji_yusu_houzhui_type'):
    #    cate = "cate"            
    else:
        cate = "cwuji_hhw_qita"
    
    return cate

def regconize_wuji(text, words, tags_chem, tags_org, tags_unorg, mask_word):
#无机
    taglist_wuji_hhw = ['cwuji_hhw', 'cwuji_hhw_yhw', 'cwuji_hhw_suan', 'cwuji_hhw_jian', 'cwuji_hhw_yan','cwuji_hhw_qita']
    taglist_wuji_yuansu = ['cyuansu_jinshu', 'cyuansu_feijinshu', 'cyuansu_xiyouqiti']# ['cwuji_yusu_danzhiqiti', 'cwuji_yusu_danzhijinshu', 'cwuji_yusu_danzhifeijinshu']
    taglist_wuji_danzhi = ['cwuji_yusu_danzhiqiti', 'cwuji_yusu_danzhijinshu', 'cwuji_yusu_danzhisu']
    #taglist_wuji_lizi = ['cwuji_yusu_muli_lizi']

    resentity_wuji = []

    resentity_wuji_danyuansu = []
    resentity_wuji_hhw_1word = []
    todoseglist = []

    start = None
    n = len(tags_unorg)
    for i in range(n):
        inyusu = False
        if (mask_word[i] == 0) and (tags_unorg[i] != '0'):
            inyusu = True
            if start == None:
                start = i

        if (start is not None) and ((i==n-1) or inyusu == False):
            segstart = start
            if inyusu == False:
                segend = i - 1
            else:
                segend = i
            #segend = i if i==len(tags_unorg)-1 else i - 1
            if segstart < segend:   #还没识别的，长度>1的无机语素
                todoseglist.append((segstart, segend))

            drop = False
            if segstart < n-1 and len(words[segstart])==1:
                word = words[segstart] + words[segstart+1]
                if word in cndict:
                    idf = cndict[word]
                    drop = True
            if segstart >0 and len(words[segstart])==1:
                word = words[segstart-1] + words[segstart]
                if word in cndict:
                    idf = cndict[word]
                    drop = True

            if segstart == segend and drop==False:   #单语素

                tag = tags_unorg[segstart]
                if tag in taglist_wuji_hhw: #整词化合物
                    cate = tag    
                    tup = (words[segstart], segstart, 1, [tag], cate)
                    resentity_wuji_hhw_1word.append(tup)
                    mask_word[segstart] = 1
                elif tag.startswith("cwuji_yusu_type"):
                    cate = "cate"
                    tup = (words[segstart], segstart, 1, [tag], cate)
                    resentity_wuji_hhw_1word.append(tup)
                    mask_word[segstart] = 1
                elif tag.startswith("cwuji_yusu_jigen_duli"):
                    cate = "cwuji_jigen"
                    tup = (words[segstart], segstart, 1, [tag], cate)
                    resentity_wuji_hhw_1word.append(tup)
                    mask_word[segstart] = 1
                elif tag in taglist_wuji_yuansu:    #单元素
                    drop = False
                    if segstart < n-1:
                        word = words[segstart] + words[segstart+1]
                        if word in cndict:
                            idf = cndict[word]
                            drop = True
                    if drop==False:
                        start_index = max(0, segstart - 3)
                        end_index = min(len(words), segend + 4)
                        prefix = words[start_index:segstart]  # start前的两个元素（如果有）
                        middle = words[segstart:segend + 1]      # start到end的元素
                        suffix = words[segend + 1:end_index]  # end后的两个元素（如果有）

                        cate = "cwuji_danzhi"
                        if tag.endswith("_jinshu"):
                            cate = "cwuji_danzhi_jinshu"
                        elif tag.endswith("_feijinshu"):
                            cate = "cwuji_danzhi_feijinshu"
                        elif tag.endswith("_xiyouqiti"):
                            cate = "cwuji_danzhi_xiyouqiti"
                        
                        tup = (words[segstart], segstart, 1, [tag], cate)
                        print("======单元素=", tup
                                , ", ", ''.join(prefix) + ' [' + ''.join(middle) + '] ' + ''.join(suffix))
                        resentity_wuji_danyuansu.append(tup)
                        mask_word[segstart] = 1
                        #print("seg=(", segstart, ",", segend, ")=")
            start = None
                
    print("======单元素=",resentity_wuji_danyuansu)
    print("======无机化合物整词=",resentity_wuji_hhw_1word)

    if len(resentity_wuji_danyuansu) > 0 :
        resentity_wuji.extend(resentity_wuji_danyuansu)
    
    if len(resentity_wuji_hhw_1word) > 0 :
        resentity_wuji.extend(resentity_wuji_hhw_1word)
    
    resentity_wuji_hhw = []
    resentity_wuji_danzhi = []

    for ele in todoseglist:
        start = ele[0]
        end = ele[1]
        if start == 1187:
            a=1
        filtered = tobeFiltered_seg_wuji(words[start:end+1], tags_unorg[start:end+1])
        
        start_index = max(0, start - 3)
        end_index = min(len(words), end + 4)

        prefix = words[start_index:start]  # start前的两个元素（如果有）
        middle = words[start:end + 1]      # start到end的元素
        suffix = words[end + 1:end_index]  # end后的两个元素（如果有）

        print("======待识别大于1的段=(", start, ",", end, "), filtered=",filtered
              , ", ", ''.join(prefix) + ' [' + ''.join(middle) + '] ' + ''.join(suffix)
              , ", ", ' + '.join(f"{word}|{tag}" for word, tag in zip(words[start:end+1], tags_unorg[start:end+1])))
        if filtered:
            continue
        
        #识别各种类型
        tag = tags_unorg[end]
        '''
        if tag == 'cwuji_yusu_houzhui_type':    #XX化合物，XX化物
            if tags_unorg[end - 1].startswith('cyuansu'):
                cate = "cate"
                resentity_wuji_hhwtype.append((words[start:end+1], start, end-start+1, tags_unorg[start:end+1], cate))
                mask_word[start: end+1] = [1] * (end - start + 1)
                continue
        '''
        new_end = end
        while new_end >= start:
            temptag = tags_unorg[new_end]
            skip = False
            if temptag in ('cwuji_yusu_jieci', 'cwuji_yusu_ccitou'):
                skip = True
            if temptag.startswith('c_biaodian_'):
                skip = True
            if temptag.endswith('_zuo') or temptag.endswith('_you'):    # or temptag.endswith('shuzi') or temptag.endswith('zimu')
                skip = True
            
            word = words[new_end]
            word2 = words[new_end-1]
            if word.isdigit() and new_end-start>=1 and contains_chinese(word2) :
                skip = True

            notrightedge = isnotrightedge(tags_unorg, words, new_end)
            if notrightedge and (new_end - start >= 1):
                skip = True

            skiplen = 1

            s = ''.join(t for t in words[start: new_end+1])            
            if len(s)>2 and s[-3]=='(' and s[-1]==')' and (s[-2] in '0123456789' or (s[-2].isalpha and s[-2].islower())):
                skiplen = 3
                skip = True

            if skip == False:
                break

            new_end -= skiplen

        new_start = start
        while new_start <= new_end:
            temptag = tags_unorg[new_start]
            skip = False
            if temptag == 'cwuji_yusu_jieci' or temptag == 'cwuji_yusu_houzhui_type':
                skip = True
            if temptag.startswith('c_biaodian_') :
                skip = True
            if temptag.endswith('_zuo') or temptag.endswith('_you'):    # or temptag.endswith('shuzi') or temptag.endswith('zimu')
                skip = True
            
            if new_start < new_end:
                word = words[new_start]
                word2 = words[new_start+1]
                if word.isdigit() and new_end-new_start>=1 and is_chinese(word2) :
                    skip = True
            notleftedge = isnotleftedge(tags_unorg, words, new_start)
            if notleftedge and (new_end - new_start >= 1):
                skip = True

            skiplen = 1
            s = ''.join(t for t in words[new_start: new_end+1])            
            if len(s)>2 and s[0]=='(' and s[2]==')' and (s[1] in '0123456789' or (s[1].isalpha and s[1].islower())):
                skiplen = 3
                skip = True

            if skip == False:
                break
            new_start += skiplen

        if new_end >= new_start:
            
            mid = int((new_start+new_end) // 2)
            if 'c_kuohao_x_zuo' in tags_unorg[mid:new_end+1] and 'c_kuohao_x_you' not in tags_unorg[mid:new_end+1]:
                for i in range(mid, new_end+1):
                    if tags_unorg[i] == 'c_kuohao_x_zuo' and i > 0:
                        new_end = i - 1
                        break
            
            mid = int((new_start+new_end) // 2)
            if 'c_kuohao_x_you' in tags_unorg[new_start:mid+1] and 'c_kuohao_x_zuo' not in tags_unorg[new_start:mid+1]:
                for i in range(new_start, mid+1):
                    if tags_unorg[i] == 'c_kuohao_x_you' and i<new_end:
                        new_start =i+1
                        break

            drop = False
            if new_start == new_end and len(words[new_end])==1:
                n = len(tags_org)
                if new_end < n-1:
                    word = words[new_end] + words[new_end+1]
                    if word in cndict:
                        idf = cndict[word]
                        drop = True

                if new_start > 0:
                    word = words[new_start-1] + words[new_start]
                    if word in cndict:
                        idf = cndict[word]
                        drop = True

            if drop==False:
                cate = cate_wuji(text, words, tags_chem, tags_org, tags_unorg, mask_word, new_start, new_end)
                assert cate in cate2id

                resentity_wuji_hhw.append((words[new_start:new_end+1], new_start, new_end-new_start+1, tags_unorg[new_start:new_end+1], cate))
                mask_word[new_start: new_end+1] = [1] * (new_end - new_start + 1)

    print("======化合物=",resentity_wuji_hhw)
    print("======单质=",resentity_wuji_danzhi)

    if len(resentity_wuji_danzhi) > 0:
        resentity_wuji.extend(resentity_wuji_danzhi)

    if len(resentity_wuji_hhw) > 0 :
        resentity_wuji.extend(resentity_wuji_hhw)

    return resentity_wuji, mask_word

def valid_cate_youji(word, tag):
    cate = ""

    if tag.startswith('cyouji_hhw'):
        cate = tag
    elif tag.startswith('cyouji_yusu_houzhui_type'):
        cate = "cate"
    elif tag.startswith('cyouji_yusu_muti_danbai'):
        cate = 'cyouji_hhw_dbz'
    elif tag.startswith('cyouji_yusu_jigen'):
        cate = "cyouji_jigen"
        if tag == 'cyouji_yusu_jigen_wujisuan':
            cate = "cyouji_hhw"

    elif tag.startswith('cyouji_yusu_fenzi'):
        cate = "cyouji_jibenlizi_fenzi"
    elif tag.startswith('cyouji_yusu_yuanzi'):
        cate = "cyouji_jibenlizi_yuanzi"
    elif tag.startswith('cyouji_yusu_lizi'):
        cate = "cyouji_jibenlizi_lizi"

    elif tag.startswith('cyuansu_jinshu'):
        cate = "cyouji_hhw_yan"
    elif tag.startswith('cyuansu_feijinshu'):
        cate = "cyouji_hhw" #待细化

    elif tag == 'cyouji_yusu_type_suan':
        cate = "cyouji_hhw_suan"
    elif tag.startswith('cyouji_yusu_type_yan'):
        cate = "cyouji_hhw_yan"
    elif tag.startswith('cyouji_yusu_type_suangan'):
        cate = "cyouji_hhw_suangan"

    elif tag.startswith('cyouji_yusu_houzhui_type'):
        cate = "cyouji_hhw"

    elif tag.startswith('cyouji_yusu_muti'):
        if tag.startswith('cyouji_yusu_muti_anjisuan'):
            cate = "cyouji_hhw_anjisuan"
        elif tag == 'cyouji_yusu_muti_huanting':
            cate = "cyouji_hhw_ting_fx"
        elif tag == 'cyouji_yusu_muti_zahuan':
            cate = "cyouji_hhw_za_qhw_zahuan"
        elif tag == 'cyouji_yusu_muti_tai':
            cate = "cyouji_hhw_tai"
        elif tag == 'cyouji_yusu_muti_hegan':
            cate = "cyouji_hhw_hegan"
        elif tag == 'cyouji_yusu_muti_hegansuan':
            cate = "cyouji_hhw_hegansuan"
        elif tag == 'cyouji_yusu_muti_tang':
            cate = "cyouji_hhw_tang"
        elif tag == 'cyouji_yusu_muti_gan':
            cate = "cyouji_hhw_tang"
        elif tag == 'cyouji_yusu_muti_tangchun':
            cate = "cyouji_hhw_tang"
        elif tag == 'cyouji_yusu_muti_tangsuan':
            cate = "cyouji_hhw_tang"
        elif tag == 'cyouji_yusu_muti_tangquansuan':
            cate = "cyouji_hhw_tang"
        elif tag == 'cyouji_yusu_muti_tanggan':
            cate = "cyouji_hhw_tang"
        elif tag == 'cyouji_yusu_muti_mei':
            cate = "cyouji_hhw_mei"
        elif tag == 'cyouji_yusu_muti_zaiti':
            cate = "cyouji_hhw_zai"
        elif tag == 'cyouji_yusu_muti_tie':
            cate = "cyouji_hhw_tie"
        elif tag == 'cyouji_yusu_muti_shengwujian':
            cate = "cyouji_hhw_shengwujian"
        elif tag == 'cyouji_yusu_muti_niao':
            cate = "cyouji_hhw_niao"
        elif tag == 'cyouji_yusu_muti_xian':
            cate = "cyouji_hhw"
        elif tag == 'cyouji_yusu_muti_zhi':
            cate = "cyouji_hhw_zhi"
        elif tag == 'cyouji_yusu_muti_neizhi':
            cate = "cyouji_hhw_neizhi"
        else:
            if word in org_word2cate:
                cate = org_word2cate[word]
    return cate

def cate_youji(text, words, tags_chem, tags_org, start, end):
    cate = 'cyouji_hhw'

    if start == end:
        tag = tags_org[start]
        word = words[start]

        if tag == 'chunhe':
            return 'hunhewu'
        
        cateword = ['酸','碱','盐','烃','烷烃','烯烃','炔烃','芳香烃','烷','烯','炔','芳烃','环烃','熳'
                    ,'酞','胺','醇','酚','醚','砜','醛','酮','醌','肟','胍','脒'
                    ,'踪','脲','酯','内酯','酰卤','酸酐','酰胺','腈','肼','生物碱','萜','甾体','糖','氨基酸'
                    ,'肽','脂','膦','胂','酶','蛋白质','苷','酐','氨基酸']
        if word in cateword:
            return "cate"
        tmpcate = valid_cate_youji(word, tag)
        if len(tmpcate) > 0:
            return tmpcate
        else:
            return cate

    else:
        for i in range(end, start - 1, -1):
            tag = tags_org[i]
            word = words[i]
            tmpcate = valid_cate_youji(word, tag)
            if len(tmpcate) > 0:
                return tmpcate

    return cate

def regconize_youji(text, words, tags_chem, tags_org, tags_unorg, mask_word):
    
    resentity_youji = []
    todoseglist = []

    resentity_youji_single = []

    start = None
    end = None
    for i in range(len(tags_org)):
        ischem = False
        if (mask_word[i] == 0) and (tags_org[i] != '0'):
            ischem = True
            if start == None:
                start = i
        
        if (start is not None):
            if ischem == False:
                end = i - 1
            else:
                if i==len(tags_org)-1:
                    end = len(tags_org) - 1
        
        if (start is not None) and (end is not None): 
            tag = tags_org[end]
            if start < end:   #还没识别的，长度>1的无机语素
                todoseglist.append((start, end))
            elif start == end:
                if tag == 'cyouji_yusu_jigen_duli':
                    cate = "cyouji_jigen"
                    resentity_youji_single.append((words[start], start, 1, [tag], cate))
                    mask_word[start: start+1] = [1] * (1)
            start = None
            end = None

    #print("======mask_youji=",mask_youji)
    
    print("======len是1的词=",resentity_youji_single)

    if len(resentity_youji_single) > 0 :
        resentity_youji.extend(resentity_youji_single)

    resentity_youji_hhw = []

    for ele in todoseglist:
        start = ele[0]
        end = ele[1]
        
        filtered = tobeFiltered_seg_youji(words[start:end+1], tags_org[start:end+1])
        
        start_index = max(0, start - 3)
        end_index = min(len(words), end + 4)

        prefix = words[start_index:start]  # start前的两个元素（如果有）
        middle = words[start:end + 1]      # start到end的元素
        suffix = words[end + 1:end_index]  # end后的两个元素（如果有）

        print("======待识别大于1的段=(", start, ",", end, "), filtered=",filtered
              , ", ", ''.join(prefix) + ' [' + ''.join(middle) + '] ' + ''.join(suffix)
              , ", ", ' + '.join(f"{word}|{tag}" for word, tag in zip(words[start:end+1], tags_org[start:end+1])))
        if filtered:
            continue
               
        #过滤尾巴噪音
        new_end = end
        while new_end >= start:
            temptag = tags_org[new_end]
            skip = False
            if temptag in ('cyouji_yusu_jieci', 'cyouji_yusu_ccitou', 'ctiangan'):
                skip = True
            if temptag.startswith('c_biaodian_'):
                skip = True
            if temptag.endswith('ccnshuzi') or temptag.endswith('ctiangan'):    # or temptag.endswith('shuzi') or temptag.endswith('zimu')
                skip = True
            if temptag.endswith('_zuo') or temptag.endswith('_you'):    # or temptag.endswith('shuzi') or temptag.endswith('zimu')
                skip = True
            if temptag == 'cyouji_yusu_jigen_qian':
                skip = True
            word = words[new_end]
            word2 = words[new_end-1]
            if word.isdigit() and new_end-start>=1 and contains_chinese(word2) :
                skip = True

            notrightedge = isnotrightedge(tags_org, words, new_end)
            if notrightedge and (new_end - start >= 1):
                skip = True

            skiplen = 1
            s = ''.join(t for t in words[start: new_end+1])            
            if len(s)>2 and s[-3]=='(' and s[-1]==')' and (s[-2] in '0123456789' or (s[-2].isalpha and s[-2].islower())):
                skiplen = 3
                skip = True

            if skip == False:
                break
            new_end -= skiplen
        
        #过滤头部噪音
        new_start = start
        while new_start <= new_end:
            temptag = tags_org[new_start]
            skip = False
            if temptag == 'cyouji_yusu_jieci':
                skip = True
            if (temptag.startswith('c_biaodian_') or temptag =='cyouji_yusu_jigen_hou'
                or temptag.startswith('cyouji_yusu_houzhui') or temptag.startswith('cyouji_yusu_houzhui_type')):
                skip = True
            if temptag.endswith('_zuo') or temptag.endswith('_you'):    # or temptag.endswith('shuzi') or temptag.endswith('zimu')
                skip = True
            word = words[new_start]
            word2 = words[new_start+1]
            if word.isdigit() and new_end-new_start>=1 and contains_chinese(word2) :
                skip = True

            notleftedge = isnotleftedge(tags_org, words, new_start)
            if notleftedge and (new_end - new_start >= 1):
                skip = True

            skiplen = 1

            s = ''.join(t for t in words[new_start: new_end+1])            
            if len(s)>2 and s[0]=='(' and s[2]==')' and (s[1] in '0123456789' or (s[1].isalpha and s[1].islower())):
                skiplen = 3
                skip = True

            if skip == False:
                break

            new_start += skiplen

        if new_end >= new_start:
            #tag = tags_org[new_end]

            is_youji = False
            for i in range(new_start, new_end + 1):
                tag = tags_org[i]
                tag_unorg = tags_unorg[i]
                if (tag.startswith('cyouji_yusu_muti') or tag.startswith('cyouji_hhw') 
                    or (tag.startswith('cyouji_yusu_jigen') and tag!="cyouji_yusu_jigen_wujisuan" and tag_unorg=="0")
                      or tag=='cyouji_yusu_ccitou_liti'
                      or tag=='cyouji_yusu_ccitou_tang' or tag=='cyouji_yusu_ccitou_tai'
                    or tag=='cyouji_yusu_jiegou'
                    or tag=='ctiangan'
                     # or tag.startswith('cyouji_yusu_type') 
                    ):
                    is_youji = True
                    break
            if is_youji:

                mid = int((new_start+new_end) // 2)
                if 'c_kuohao_x_zuo' in tags_org[mid:new_end+1] and 'c_kuohao_x_you' not in tags_org[mid:new_end+1]:
                    for i in range(mid, new_end+1):
                        if tags_org[i] == 'c_kuohao_x_zuo' and i > 0:
                            new_end = i - 1
                            break
                
                mid = int((new_start+new_end) // 2)
                if 'c_kuohao_x_you' in tags_org[new_start:mid+1] and 'c_kuohao_x_zuo' not in tags_org[new_start:mid+1]:
                    for i in range(new_start, mid+1):
                        if tags_org[i] == 'c_kuohao_x_you' and i<new_end:
                            new_start =i+1
                            break

                drop = False
                if new_start == new_end and len(words[new_end])==1:
                    n = len(tags_org)
                    if new_end < n-1:
                        word = words[new_end] + words[new_end+1]
                        if word in cndict:
                            idf = cndict[word]
                            drop = True

                    if new_start > 0:
                        word = words[new_start-1] + words[new_start]
                        if word in cndict:
                            idf = cndict[word]
                            drop = True

                if drop == False:
                    pos = new_end
                    for i in range(new_end, new_start-1, -1):
                        tag = tags_org[i]
                        if not ( tag.startswith('c_biaodian') or tag.startswith('c_kuohao')
                            or tag.endswith('shuzi') or tag.endswith('zimu') ):
                            pos = i
                            break
                    
                    tag = tags_org[pos] if pos>=new_start else tags_org[new_end]

                    cate = cate_youji(text, words, tags_chem, tags_org, new_start, pos)

                    resentity_youji_hhw.append((words[new_start:new_end+1], new_start, new_end-new_start+1, tags_org[new_start:new_end+1], cate))
                    mask_word[new_start: new_end+1] = [1] * (new_end - new_start + 1)
        
    print("======化合物=\n", '\n'.join(f'({x}, {y}, {z}, {w}, {v})' for x, y, z, w, v in resentity_youji_hhw))
    
    if len(resentity_youji_hhw) > 0 :
        resentity_youji.extend(resentity_youji_hhw)

    #有机化合物，整词
    resentity_youji_hhw_1word = []
    for index, tag in enumerate(tags_org):
        if mask_word[index] == 1:
            continue
        
        if tag.startswith('cyouji_hhw') or tag.startswith('cyouji_yusu_muti') or tag.startswith('chunhe'):
            
            notleftedge = isnotleftedge(tags_org, words, index)
            if notleftedge:
                continue

            notrightedge = isnotrightedge(tags_org, words, index)
            if notrightedge:
                continue

            mask_word[index] = 1
            
            cate = cate_youji(text, words, tags_chem, tags_org, index, index)

            resentity_youji_hhw_1word.append((words[index], index, 1, [tag], cate))
            
    print("======有机化合物整词=\n", '\n'.join(f'({x}, {y}, {z}, {w}, {v})' for x, y, z, w, v in resentity_youji_hhw_1word))

    if len(resentity_youji_hhw_1word) > 0 :
        resentity_youji.extend(resentity_youji_hhw_1word)

    return resentity_youji, mask_word
    
def regentity(text):

    #zhwords = matcher.segment_zh(text)
    #words, tags_chem, tags_org, tags_unorg = matcher.segment_chem_words(zhwords)
    
    words, tags_chem, tags_org, tags_unorg = matcher.segment_chem_text(text)

    assert len(words) ==  len(tags_chem) == len(tags_org) == len(tags_unorg)
    
    s = ''.join(w for w in words)
    assert text == s

    print("text = ", text)
    print("words = ", words)
    print("\ntags_chem= ", [f"{words[i]}/{tags_chem[i]}" for i in range(len(words))])
    print("\ntags_org= ", [f"{words[i]}/{tags_org[i]}" for i in range(len(words))])
    print("\ntags_unorg= ", [f"{words[i]}/{tags_unorg[i]}" for i in range(len(words))])
    print("\n")

    mask_word = [0] * len(words)

    resentity_youji, mask_word = regconize_youji(text, words, tags_chem, tags_org, tags_unorg, mask_word)

    resentity_wuji, mask_word = regconize_wuji(text, words, tags_chem, tags_org, tags_unorg, mask_word)

    resentity = []
    if len(resentity_youji) > 0:
        resentity.extend(tup for tup in resentity_youji)
    if len(resentity_wuji) > 0:
        resentity.extend(tup for tup in resentity_wuji)

    return resentity, words, tags_chem, tags_org, tags_unorg

def convert_indices(text, words, resentity):
    # 用于存储每个词在text中的起始位置
    word_start_indices = []
    current_index = 0

    # 遍历words，记录每个词在text中的起始位置
    for word in words:
        word_start_indices.append(current_index)
        current_index += len(word)

    assert current_index==len(text)

    # 将resentity中的word下标转换为text下标
    converted_resentity = []
    for tup in resentity:
        terms = tup[0]
        start = tup[1]
        end = start + tup[2] - 1
        tagarr = tup[3]
        tag = tup[4]

        if tag not in cate2id:
            print("==========tag=",tag, ", terms=",terms)

        assert tag in cate2id

        id = "3"
        if tag in cate2id:
            id = cate2id[tag]

        total_length = 0
        for i in range(start, end + 1):
            w = words[i]
            total_length += len(w)

        word = ''.join(term for term in terms)

        start_text = word_start_indices[start]

        assert text[start_text:start_text+total_length] == word

        converted_resentity.append((word, start_text, total_length, tagarr, id))

    return converted_resentity

def read_file_and_replace_newlines(file_path):
    with open(file_path, 'r', encoding='utf-8-sig') as file:
        content = file.read()
        content_with_crnl = content.replace('\n\n\n', '\n').replace('\n\n', '\n').replace('\n', '\r\n')
        return content_with_crnl
    
textlist = []

filenames = [
            "./ziliao/yuliao/des/c07b-400.txt"
             ]
outfile_path = './ziliao/yuliao/des/c07b-50des.json'

danpian= False
if danpian:
    for name in filenames:
        text = read_file_and_replace_newlines(name)
        text = fullwidth_to_halfwidth(text)
        text = text.replace(' ', '').lower()
        textlist.append(text)
else:
    outfile_path = './ziliao/yuliao/des/c07g-50des.json'
    file = open("./ziliao/yuliao/des/c07g-72.txt", 'r', encoding='utf-8-sig')
    cnt = 0
    for line in file:
        line = line.rstrip('\n')
        line = line.replace("huanhanghuanhanghuanhang","\n")
        line = line.replace("huanhanghuanhang","\n")
        line = line.replace("huanhang","\n")
        line = fullwidth_to_halfwidth(line)
        line = line.replace(' ', '').lower()
        textlist.append(line)
        cnt += 1
        if cnt >= 50: break

#textlist.append("氢氧化钠，氦气，金属钠，氯气，氯，氧化锕，氯化铁，钠离子，氢原子")
text = "金茂"  #,lda(二异丙基氨基锂)或直接
text = fullwidth_to_halfwidth(text)
text = text.replace(' ', '').lower()
#textlist.append(text)

annofile = open(outfile_path, 'w', encoding='utf-8')

jsonarr = []

for text in textlist:
    if text.find("氢氧化镍")>0:
        a=1

    resentity, words, tags_chem, tags_org, tags_unorg = regentity(text)

    converted_resentity = convert_indices(text, words, resentity)

    #print("======text=", text)
    #print("======convert_indices=", '\n'.join(f'({x}, {y}, {z}, {w}, {v})' for x, y, z, w, v in converted_resentity))

    res = {}
    res["text"] = text
    entities_value = []
    i = 0
    for x, y, z, w, v in converted_resentity:
        #term, start_index_in_text, total_length, tagarr, tmp
        t = {}
        t["id"]=i
        t["label"]=v
        t["startOffset"]=y
        t["endOffset"]=y+z
        t["text"]=x
        t["type"]=1
        entities_value.append(t)
        i+=1
    res["entities"] = entities_value
    jsonarr.append(res)
    
    #restext = highlight_entity_text(text, converted_resentity)
    restext = highlight_entity(words, resentity)
    print("======restext=", restext)

    #fileres.write("doctext: "+text + '\n')
    fileres.write("rulebased: "+restext + '\n')
    #fileres.write('==============================\n\n')

    print("====================================================")

json.dump(jsonarr, annofile, ensure_ascii=False, indent=4)

fileres.close()
annofile.close()
