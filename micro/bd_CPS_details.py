def text_repl(string_item):
    return (string_item.replace('PEAGE', 'PRTAGE').replace('PTERNHLY', 'PRERNHLY')
            .replace('PTERNWA', 'PRERNWA').replace('GEMETSTA', 'GTMETSTA')
            .replace('PERACE', 'PRDTRACE').replace('PTDTRACE', 'PRDTRACE')
            .replace('HRHHID (partII)', 'HRHHID2').replace('PRORIGIN', 'PRDTHSP')
            .replace('PTIO1OCD', 'PEIO1OCD'))


VarList = ['PWORWGT', 'PWCMPWGT', 'PWLGWGT', 'PRERNWA',
           'PTERNWA', 'PWSSWGT', 'HRHHID (partII)',
           'HRHHID2', 'HRYEAR', 'HRYEAR4', 'PRERNHLY',
           'PTERNHLY', 'HRMONTH', 'PESEX', 'PEMLR',
           'PENLFRET', 'PENLFACT', 'PRDISC', 'GESTFIPS',
           'HRMIS', 'PRCOW1', 'PRFTLF', 'PREMPNOT',
           'PRCIVLF', 'PEJHRSN', 'PRSJMJ', 'PEEDUCA',
           'PRWKSTAT', 'PRMJOCC1', 'GTMETSTA', 'GEMETSTA',
           'PEDWWNTO', 'PRUNTYPE', 'PRMJIND1', 'GTCBSA',
           'PERACE', 'PTDTRACE', 'PRDTRACE', 'PRORIGIN',
           'HUHHNUM', 'PRDTHSP', 'PRCHLD', 'PRTAGE',
           'PEAGE', 'PULINENO', 'PRWNTJOB', 'PEERNLAB',
           'PRUNEDUR', 'PEHRUSL1', 'PRMARSTA', 'PRCITSHP',
           'PRDTOCC1', 'PRDTIND1', 'PUIODP1', 'PUIODP2',
           'PEIO1COW', 'PEIO1OCD', 'PEIO1ICD', 'PEIO2COW',
           'HRHHID', 'HRSAMPLE', 'HRSERSUF', 'PTIO1OCD',
           'PRDISFLG']

DataDict = {'January_2017_Record_Layout.txt':
            {'start': '2017-01-01', 'end': '2018-12-01',
             're': f'({"|".join(VarList)})\s+(\d+)\s+.*?\t+.*?(\d\d*).*?(\d\d+)'},
            'January_2015_Record_Layout.txt':
            {'start': '2015-01-01', 'end': '2016-12-31',
             're': f'({"|".join(VarList)})\s+(\d+)\s+.*?\t+.*?(\d\d*).*?(\d\d+)'},
            'January_2014_Record_Layout.txt':
            {'start': '2014-01-01', 'end': '2014-12-31',
             're': f'({"|".join(VarList)})\s+(\d+)\s+.*?\t+.*?(\d\d*).*?(\d\d+)'},
            'January_2013_Record_Layout.txt':
            {'start': '2013-01-01', 'end': '2013-12-31',
             're': f'({"|".join(VarList)})\s+(\d+)\s+.*?\t+.*?(\d\d*).*?(\d\d+)'},
            'may12dd.txt':
            {'start': '2012-05-01', 'end': '2012-12-31',
             're': f'({"|".join(VarList)})\s+(\d+)\s+.*?\t+.*?(\d\d*).*?(\d\d+)'},
            'jan10dd.txt':
            {'start': '2010-01-01', 'end': '2012-04-30',
             're': f'\n(?:\x0c)?({"|".join(VarList)})\s+(\d+)\s+.*? \s+.*?(\d\d*).*?(\d\d+)'},
            'jan09dd.txt':
            {'start': '2009-01-01', 'end': '2009-12-31',
             're': f'\n(?:\x0c)?({"|".join(VarList)})\s+(\d+)\s+.*? \s+.*?(\d\d*).*?(\d\d+)'},
            'jan07dd.txt':
            {'start': '2007-01-01', 'end': '2008-12-31',
             're': f'\n(?:\x0c)?({"|".join(VarList)})\s+(\d+)\s+.*? \s+.*?(\d\d*).*?(\d\d+)'},
            'augnov05dd.txt':
            {'start': '2005-08-01', 'end': '2006-12-31',
             're': f'\n(?:\x0c)?({"|".join(VarList)})\s+(\d+)\s+.*? \s+.*?(\d\d*).*?(\d\d+)'},
            'may04dd.txt':
            {'start': '2004-05-01', 'end': '2005-7-31',
             're': f'\n(?:\x0c)?({"|".join(VarList)})\s+(\d+)\s+.*? \s+.*?(\d\d*).*?(\d\d+)'},
            'jan03dd.txt':
            {'start': '2003-01-01', 'end': '2004-04-30',
             're': f'\n(?:\x0c)?({"|".join(VarList)})\s+(\d+)\s+.*? \s+.*?(\d\d*).*?(\d\d+)'},
            'jan98dd.asc':
            {'start': '1998-01-01', 'end': '2002-12-31',
             're': 'D (\w+)\s+(\d{1,2})\s+(\d+)\s+'},
            'sep95_dec97_dd.txt':
            {'start': '1995-09-01', 'end': '1997-12-31',
             're': f'\n(?:\x0c)?({"|".join(VarList)})\s+(\d+)\s+.*? \s+.*?(\d\d*).*?(\d\d+)'},
            'jun95_aug95_dd.txt':
            {'start': '1995-06-01', 'end': '1995-08-31',
             're': f'\n(?:\x0c)?({"|".join(VarList)})\s+(\d+)\s+.*? \s+.*?(\d\d*).*?(\d\d+)'},
            'apr94_may95_dd.txt':
            {'start': '1994-04-01', 'end': '1995-05-31',
             're': f'\n(?:\x0c)?({"|".join(VarList)})\s+(\d+)\s+.*? \s+.*?(\d\d*).*?(\d\d+)'},
            'jan94_mar94_dd.txt':
            {'start': '1994-01-01', 'end': '1995-03-31',
             're': f'\n(?:\x0c)?({"|".join(VarList)})\s+(\d+)\s+.*? \s+.*?(\d\d*).*?(\d\d+)'}}
