#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import sys
from math import log
from collections import Counter
import numpy as np
import pandas as pd

max_word_len = 6
re_chinese = re.compile(u"[\w]+", re.U)

def count_words(lines):
    word_freq = Counter()
    for line in lines:
        words = []
        for sentence in re_chinese.findall(line):
            length = len(sentence)
            for i in range(length):
                words += [sentence[i: j + i] for j in range(1, min(length - i + 1, max_word_len + 1))]
        word_freq.update(words)
    
    return word_freq


def lrg_info(word_freq, total_word, min_freq, min_mtro):
    l_dict = {}
    pmi_l_dict = {}
    r_dict = {}
    pmi_r_dict = {}
    for word, freq in word_freq.items():
        if len(word) < 3:
            continue

        left_word = word[:-1]
        right_word = word[1:]

        def __update_dict(side_dict, pmi_side_dict, side_word):
            side_word_freq = word_freq[side_word]
            if side_word_freq > min_freq:
                mul_info1 = side_word_freq * total_word / (word_freq[side_word[1:]] * word_freq[side_word[0]])
                mul_info2 = side_word_freq * total_word / (word_freq[side_word[-1]] * word_freq[side_word[:-1]])
                mul_info = min(mul_info1, mul_info2)
                if mul_info > min_mtro:
                    pmi_side_dict[side_word] = mul_info
                    if side_word in side_dict:
                        side_dict[side_word].append(freq)                  
                    else:
                        side_dict[side_word] = [side_word_freq, freq]

        __update_dict(l_dict, pmi_l_dict, left_word)
        __update_dict(r_dict, pmi_r_dict, right_word)

    return l_dict, pmi_l_dict, r_dict, pmi_r_dict


def cal_entro(r_dict):
    entro_r_dict = {}
    for word in r_dict:
        m_list = r_dict[word]

        r_list = m_list[1:]

        entro_r = 0
        sum_r_list = sum(r_list)
        for rm in r_list:
            entro_r -= rm / sum_r_list * log(rm / sum_r_list, 2)
        entro_r_dict[word] = entro_r

    return entro_r_dict


def entro_lr_fusion(entro_r_dict, entro_l_dict):
    entro_in_rl_dict = {}
    entro_in_r_dict = {}
    entro_in_l_dict = entro_l_dict.copy()
    for word in entro_r_dict:
        if word in entro_l_dict:
            entro_in_rl_dict[word] = [entro_l_dict[word], entro_r_dict[word]]
            entro_in_l_dict.pop(word)
        else:
            entro_in_r_dict[word] = entro_r_dict[word]
    return entro_in_rl_dict, entro_in_l_dict, entro_in_r_dict


def entro_filter(entro_in_rl_dict, entro_in_l_dict, entro_in_r_dict, pmi_l_dict, pmi_r_dict, word_freq, min_entro):
    word_dict = {}
    
    for word in entro_in_rl_dict:
        rl_min_entro = min(entro_in_rl_dict[word][0],entro_in_rl_dict[word][1])
        rl_min_pmi = min(pmi_l_dict[word],pmi_r_dict[word])
        if rl_min_entro > min_entro:
            try:
                word_dict[word] = [word_freq[word],rl_min_pmi,rl_min_entro]
            except:
#                 print('error: ',word)
                word_dict[word] = [word_freq[word]]
                continue
    for word in entro_in_l_dict:
        if entro_in_l_dict[word] > min_entro:
            try:  
                word_dict[word] = [word_freq[word],pmi_l_dict[word],entro_in_l_dict[word]]
            except:
                word_dict[word] = [word_freq[word]]
                continue
    for word in entro_in_r_dict:
        if entro_in_r_dict[word] > min_entro:
            try:
                word_dict[word] = [word_freq[word],pmi_r_dict[word],entro_in_r_dict[word]]
            except:
                word_dict[word] = [word_freq[word]]
                continue
    return word_dict

def min_max_normalization(word_dict):
    min_freq = min([v[1][0] for v in word_dict.items()])
    max_freq = max([v[1][0] for v in word_dict.items()])
    delta_freq = max_freq-min_freq
    min_pmi = min([v[1][1] for v in word_dict.items()])
    max_pmi = max([v[1][1] for v in word_dict.items()])
    delta_pmi = max_pmi-min_pmi
    min_entro = min([v[1][2] for v in word_dict.items()])
    max_entro = max([v[1][2] for v in word_dict.items()])
    delta_entro = max_entro-min_entro
    # min max normalization
    normalized_word_dict = word_dict.copy()
    for word in normalized_word_dict:
        normalized_word_dict[word][0] = (word_dict[word][0]-min_freq)/delta_freq
        normalized_word_dict[word][1] = (word_dict[word][1]-min_pmi)/delta_pmi
        normalized_word_dict[word][2] = (word_dict[word][2]-min_entro)/delta_entro
    return normalized_word_dict

def cal_score(word_dict):
    score = {}
    for word in word_dict:
        score[word] = np.mean(word_dict[word])
    return score

def new_words_find(sentences, min_freq=10, min_mtro=80, min_entro=3):
    word_freq = count_words(sentences)
    total_word = sum(word_freq.values())

    l_dict, pmi_l_dict, r_dict, pmi_r_dict = lrg_info(word_freq, total_word, min_freq, min_mtro)

    entro_r_dict = cal_entro(l_dict)
    entro_l_dict = cal_entro(r_dict)

    entro_in_rl_dict, entro_in_l_dict, entro_in_r_dict = entro_lr_fusion(entro_r_dict, entro_l_dict)
    word_dict = entro_filter(entro_in_rl_dict, entro_in_l_dict, entro_in_r_dict, pmi_l_dict, pmi_r_dict, word_freq, min_entro)
#     normalized_word_dict = min_max_normalization(word_dict)
    result = sorted(word_dict.items(), key=lambda x: x[1][0], reverse=True)
#     score = cal_score(normalized_word_dict)
#     score = sorted(score.items(),key=lambda x:x[1],reverse=True)
    return result
   
  
 
