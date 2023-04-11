import argparse
import json
import os
import random
import html
import re

parser = argparse.ArgumentParser(prog='qmixer', description='exam question randomizer')
parser.add_argument('-c', '--code', default='101', help='questions code')
parser.add_argument('-s', '--start', type=int, default=1, help='beginning question number')
parser.add_argument('infile', help='source JSON file (see sample.json)')
parser.add_argument('out_q', help='questions output file')
parser.add_argument('out_a', help='answers output file')

args = parser.parse_args()

with open(args.infile, 'r', encoding='utf-8') as f:
    input_data = json.load(f)

total_q = 0 # number of questions
for qgroup in input_data['qgroups']: total_q += len(qgroup['questions'])

formatting = []
for mode in input_data['template']['formatting']:
    formatting.append((mode['min_chars'], mode['ans_per_line']))
formatting = sorted(formatting, reverse=True)

print(f'Loaded {total_q} question(s) from {args.infile}.')

fo_q = open(args.out_q, 'w', encoding='utf-8')
fo_a = open(args.out_a, 'w', encoding='ascii')

# write answer header
fo_a.write('Code\\Question,' + ','.join([str(x) for x in range(1, total_q+1)]) + f'\n{args.code},')

# write header
stylesheet = input_data['template'].get('stylesheet', '')
fo_q.write(f'<!DOCTYPE html>\n<html><head><link rel="stylesheet" href="{stylesheet}"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head><body>\n<header>\n')
with open(input_data['template']['begin'], 'r', encoding='utf-8') as f: fo_q.write(f.read().format(q_code = args.code))
fo_q.write('\n</header>\n')

q_num = args.start # question number

# find suitable formatting for specified maximum answer length
def find_formatting(maxlen):
    fmt_type = None
    for fmt in formatting:
        if maxlen >= fmt[0]:
            fmt_type = fmt
            break
    assert fmt_type is not None
    return fmt_type

qgroups = list(range(len(input_data['qgroups'])))
if input_data.get('mix_groups', True): random.shuffle(qgroups)
for i in qgroups:
    print(f'Mixing question group #{i+1}...', end='')
    qgroup = input_data['qgroups'][i]

    s = '<section>\n'
    q_nums = list(range(q_num, q_num+len(qgroup['questions'])+1))
    if not (qgroup.get('qg_text') is None):
        qg_template = input_data['template'].get('qgroup', '{qg_text}')
        # print(q_nums)
        s += '<div>' + qg_template.format(qg_text=qgroup['qg_text'].format(*q_nums), qg_num=i+1) + '</div>\n'
    if not (qgroup.get('question') is None): s += '<div>' + qgroup['question'].format(*q_nums) + '</div>\n'
    fo_q.write(s)

    # check if we can turn the whole group into a table
    qg_table = True
    n_ans = len(qgroup['questions'][0]['answers'])
    fmt = find_formatting(max([len(html.unescape(re.sub('<[^<]+?>', '', x))) for x in qgroup['questions'][0]['answers']]))

    for q in qgroup['questions']: # all questions must have no text and must have same formatting type and number of answers
        if len(q.get('q_text', '')) > 0 or len(q['answers']) != n_ans or find_formatting(max([len(html.unescape(re.sub('<[^<]+?>', '', x))) for x in q['answers']])) != fmt:
            qg_table = False
            break
    
    if qg_table: fo_q.write('<table style="width:100%;border-collapse:collapse;">\n')

    questions = list(range(len(qgroup['questions'])))
    if not qgroup.get('no_mix', False): random.shuffle(questions)
    for j in questions:
        question = qgroup['questions'][j]
        answers = []
        max_chars = 0
        for k, ans in enumerate(question['answers']):
            answers.append((ans, (k == question['correct'])))
            max_chars = max(max_chars, len(html.unescape(re.sub('<[^<]+?>', '', ans))))
        if not question.get('no_mix', False): random.shuffle(answers)
        fmt_type = find_formatting(max_chars)
        #print(question.get('q_text', ''), end=': ')
        #print(fmt_type)
        if qg_table:
            # form question as table
            fo_q.write('<tr class="question"><td style="white-space:nowrap;">' + input_data['template']['question'].format(q_num=q_num) + '</td><td style="width:2px;"></td><td><table style="table-layout:fixed;width:100%;border-collapse:collapse;">')
        else:
            # answers on the next line
            fo_q.write('<div class="question">' + input_data['template']['question'].format(q_num=q_num) + question.get('q_text', '') + '<br>\n<table style="table-layout:fixed;width:100%;border-collapse:collapse;">')
        ans_letter = 'A'
        first_row = True
        for k, ans in enumerate(answers):
            if k % fmt_type[1] == 0:
                if not first_row: fo_q.write('</tr>\n')
                fo_q.write('<tr>\n')
                first_row = False
            fo_q.write('<td>' + input_data['template']['answer'].format(a_letter=ans_letter, a_text=ans[0]) + '</td>\n')
            if ans[1]: fo_a.write(ans_letter)
            ans_letter = chr(ord(ans_letter[0])+1)
        fo_q.write('</tr>\n</table>\n'+('</td></tr>\n' if qg_table else '</div>')+'\n')
        if q_num != total_q: fo_a.write(',')
        q_num += 1
    
    if qg_table: fo_q.write('</table>\n')

    fo_q.write('</section>\n')
    print('done.')

# write footer
fo_q.write('\n<footer>\n')
with open(input_data['template']['end'], 'r', encoding='utf-8') as f: fo_q.write(f.read().format(q_code = args.code))
fo_q.write('\n</footer>\n</body></html>')

fo_q.close()
fo_a.close()