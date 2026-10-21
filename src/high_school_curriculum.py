# -*- coding: utf-8 -*-
"""
High School Curriculum Engine for Moroccan Qualifying Secondary Education (الثانوي التأهيلي)
Compliant with:
- Ministerial Circular No. 43 (22 March 2006)
- Ministerial Circular No. 133-14 (International Streams / French Option BIOF)
- Ministerial Circular No. 040-19 (Vocational Baccalaureate)
Legal Teacher Quota: 21 Hours / Week
"""

import math
from typing import Dict, List, Any

true = True
false = False
null = None

# Subject definitions and standard codes
HIGH_SCHOOL_SUBJECTS = {
    "PC": "الفيزياء والكيمياء",
    "SVT": "علوم الحياة  والأرض",
    "M": "الرياضيات",
    "A": "اللغة  العربية",
    "F": "اللغة  الفرنسية",
    "ENG": "اللغة الإنجليزية",
    "HG": "التاريخ والجغرافيا",
    "I": "التربية الإسلامية",
    "PH": "الفلسفة",
    "EPS": "التربية البدنية والرياضة",
    "INF": "المعلوميات",
    "TR": "الترجمة",
    "SI": "علوم المهندس",
    "COMP": "المحاسبة",
    "EGS": "الاقتصاد العام والاحصاء",
    "ORG": "الاقتصاد والتنظيم الإداري للمقاولات",
    "DR": "القانون",
    "IG": "معلوميات التدبير",
    "IINF": "المعلوميات والانفوغرافيا",
    "DEP": "الرسم والتعبير التشكيلي",
    "CPHA": "الثقافة التشكيلية وتاريخ الفن",
    "AG": "فنون الغرافيك",
    "V": "الحجم",
    "COM": "تصميم التواصل",
    "ENV": "تصميم المحيط",
    "PROD": "تصميم المنتوج",
    "FO": "الفقه والأصول",
    "TH": "التفسير والحديث",
    "DOC": "التوثيق",
    "FT": "الفرائض والتوقيت"
}

# All Moroccan Qualifying Secondary Streams
HIGH_SCHOOL_STREAMS = [
    {
        "id": "tc_sc",
        "name": "الجذع المشترك العلمي",
        "level": "TC",
        "level_num": 1,
        "level_name": "الجذوع المشتركة",
        "category": "الشعب العامة والدولية",
        "subjects": {
            "PC": {
                "code": "PC",
                "name": "الفيزياء والكيمياء",
                "hours": 4,
                "split": "4",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "SVT": {
                "code": "SVT",
                "name": "علوم الحياة  والأرض",
                "hours": 3,
                "split": "3",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 5,
                "split": "5",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "HG": {
                "code": "HG",
                "name": "التاريخ والجغرافيا",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            },
            "INF": {
                "code": "INF",
                "name": "المعلوميات",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة الإعلاميات",
                "is_grouped": false
            }
        }
    },
    {
        "id": "tc_sc_biof",
        "name": "الجذع المشترك العلمي - دولي",
        "level": "TC",
        "level_num": 1,
        "level_name": "الجذوع المشتركة",
        "category": "الشعب العامة والدولية",
        "subjects": {
            "PC": {
                "code": "PC",
                "name": "الفيزياء والكيمياء",
                "hours": 4,
                "split": "2+2G",
                "room_type": "مختبر علمي",
                "is_grouped": true
            },
            "SVT": {
                "code": "SVT",
                "name": "علوم الحياة  والأرض",
                "hours": 3,
                "split": "1+2G",
                "room_type": "مختبر علمي",
                "is_grouped": true
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 5,
                "split": "2+2+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 6,
                "split": "2+2+1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "1+1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "HG": {
                "code": "HG",
                "name": "التاريخ والجغرافيا",
                "hours": 2,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 2,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "1+1",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            },
            "INF": {
                "code": "INF",
                "name": "المعلوميات",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة الإعلاميات",
                "is_grouped": false
            }
        }
    },
    {
        "id": "tc_lsh",
        "name": "الجذع المشترك للآداب والعلوم الإنسانية",
        "level": "TC",
        "level_num": 1,
        "level_name": "الجذوع المشتركة",
        "category": "الشعب العامة والدولية",
        "subjects": {
            "SVT": {
                "code": "SVT",
                "name": "علوم الحياة  والأرض",
                "hours": 1,
                "split": "1",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 5,
                "split": "5",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "HG": {
                "code": "HG",
                "name": "التاريخ والجغرافيا",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            },
            "INF": {
                "code": "INF",
                "name": "المعلوميات",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة الإعلاميات",
                "is_grouped": false
            }
        }
    },
    {
        "id": "tc_lsh_biof",
        "name": "الجذع المشترك للآداب والعلوم الإنسانية - دولي فرنسية",
        "level": "TC",
        "level_num": 1,
        "level_name": "الجذوع المشتركة",
        "category": "الشعب العامة والدولية",
        "subjects": {
            "SVT": {
                "code": "SVT",
                "name": "علوم الحياة  والأرض",
                "hours": 1,
                "split": "1+2G",
                "room_type": "مختبر علمي",
                "is_grouped": true
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 2,
                "split": "2+2+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 5,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 8,
                "split": "2+2+1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 4,
                "split": "1+1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "HG": {
                "code": "HG",
                "name": "التاريخ والجغرافيا",
                "hours": 4,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 2,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "1+1",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            },
            "INF": {
                "code": "INF",
                "name": "المعلوميات",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة الإعلاميات",
                "is_grouped": false
            }
        }
    },
    {
        "id": "1bac_exp",
        "name": "الأولى باكالوريا علوم تجريبية",
        "level": "1BAC",
        "level_num": 2,
        "level_name": "السنة الأولى باكالوريا",
        "category": "الشعب العامة والدولية",
        "subjects": {
            "PC": {
                "code": "PC",
                "name": "الفيزياء والكيمياء",
                "hours": 4,
                "split": "4",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "SVT": {
                "code": "SVT",
                "name": "علوم الحياة  والأرض",
                "hours": 4,
                "split": "4",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 5,
                "split": "5",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "HG": {
                "code": "HG",
                "name": "التاريخ والجغرافيا",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            }
        }
    },
    {
        "id": "1bac_exp_biof",
        "name": "الأولى باكالوريا علوم تجريبية - دولي فرنسية",
        "level": "1BAC",
        "level_num": 2,
        "level_name": "السنة الأولى باكالوريا",
        "category": "الشعب العامة والدولية",
        "subjects": {
            "PC": {
                "code": "PC",
                "name": "الفيزياء والكيمياء",
                "hours": 4,
                "split": "2+2G",
                "room_type": "مختبر علمي",
                "is_grouped": true
            },
            "SVT": {
                "code": "SVT",
                "name": "علوم الحياة  والأرض",
                "hours": 4,
                "split": "1+2G",
                "room_type": "مختبر علمي",
                "is_grouped": true
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 5,
                "split": "2+2+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 6,
                "split": "2+2+1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "1+1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "HG": {
                "code": "HG",
                "name": "التاريخ والجغرافيا",
                "hours": 2,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 2,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "1+1",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            }
        }
    },
    {
        "id": "1bac_sm",
        "name": "الأولى باكالوريا علوم رياضية",
        "level": "1BAC",
        "level_num": 2,
        "level_name": "السنة الأولى باكالوريا",
        "category": "الشعب العامة والدولية",
        "subjects": {
            "PC": {
                "code": "PC",
                "name": "الفيزياء والكيمياء",
                "hours": 5,
                "split": "5",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "SVT": {
                "code": "SVT",
                "name": "علوم الحياة  والأرض",
                "hours": 2,
                "split": "2",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 7,
                "split": "7",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "HG": {
                "code": "HG",
                "name": "التاريخ والجغرافيا",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            }
        }
    },
    {
        "id": "1bac_sm_biof",
        "name": "الأولى باكالوريا علوم رياضية - دولي فرنسية",
        "level": "1BAC",
        "level_num": 2,
        "level_name": "السنة الأولى باكالوريا",
        "category": "الشعب العامة والدولية",
        "subjects": {
            "PC": {
                "code": "PC",
                "name": "الفيزياء والكيمياء",
                "hours": 5,
                "split": "2+2G",
                "room_type": "مختبر علمي",
                "is_grouped": true
            },
            "SVT": {
                "code": "SVT",
                "name": "علوم الحياة  والأرض",
                "hours": 2,
                "split": "1+2G",
                "room_type": "مختبر علمي",
                "is_grouped": true
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 7,
                "split": "2+2+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 6,
                "split": "2+2+1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "1+1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "HG": {
                "code": "HG",
                "name": "التاريخ والجغرافيا",
                "hours": 2,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 2,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "1+1",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            }
        }
    },
    {
        "id": "1bac_lsh",
        "name": "الأولى باكالوريا آداب وعلوم إنسانية",
        "level": "1BAC",
        "level_num": 2,
        "level_name": "السنة الأولى باكالوريا",
        "category": "الشعب العامة والدولية",
        "subjects": {
            "SVT": {
                "code": "SVT",
                "name": "علوم الحياة  والأرض",
                "hours": 1,
                "split": "1",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 5,
                "split": "5",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 5,
                "split": "5",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "HG": {
                "code": "HG",
                "name": "التاريخ والجغرافيا",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            }
        }
    },
    {
        "id": "1bac_lsh_biof",
        "name": "الأولى باكالوريا آداب وعلوم إنسانية - - دولي فرنسية",
        "level": "1BAC",
        "level_num": 2,
        "level_name": "السنة الأولى باكالوريا",
        "category": "الشعب العامة والدولية",
        "subjects": {
            "SVT": {
                "code": "SVT",
                "name": "علوم الحياة  والأرض",
                "hours": 1,
                "split": "1+2G",
                "room_type": "مختبر علمي",
                "is_grouped": true
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 2,
                "split": "2+2+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 5,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 8,
                "split": "2+2+1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 4,
                "split": "1+1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "HG": {
                "code": "HG",
                "name": "التاريخ والجغرافيا",
                "hours": 4,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 2,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "1+1",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            }
        }
    },
    {
        "id": "2bac_pc",
        "name": "الثانية باكالوريا علوم فيزيائية",
        "level": "2BAC",
        "level_num": 3,
        "level_name": "السنة الثانية باكالوريا",
        "category": "الشعب العامة والدولية",
        "subjects": {
            "PC": {
                "code": "PC",
                "name": "الفيزياء والكيمياء",
                "hours": 8,
                "split": "8",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "SVT": {
                "code": "SVT",
                "name": "علوم الحياة  والأرض",
                "hours": 6,
                "split": "6",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 5,
                "split": "5",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 1,
                "split": "1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            }
        }
    },
    {
        "id": "2bac_svt",
        "name": "الثانية باكالوريا علوم الحياة والأرض",
        "level": "2BAC",
        "level_num": 3,
        "level_name": "السنة الثانية باكالوريا",
        "category": "الشعب العامة والدولية",
        "subjects": {
            "PC": {
                "code": "PC",
                "name": "الفيزياء والكيمياء",
                "hours": 6,
                "split": "6",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "SVT": {
                "code": "SVT",
                "name": "علوم الحياة  والأرض",
                "hours": 8,
                "split": "8",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 5,
                "split": "5",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 1,
                "split": "1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            }
        }
    },
    {
        "id": "2bac_l",
        "name": "الثانية باكالوريا آداب",
        "level": "2BAC",
        "level_num": 3,
        "level_name": "السنة الثانية باكالوريا",
        "category": "الشعب العامة والدولية",
        "subjects": {
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 5,
                "split": "5",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 5,
                "split": "5",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 5,
                "split": "5",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "HG": {
                "code": "HG",
                "name": "التاريخ والجغرافيا",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            }
        }
    },
    {
        "id": "2bac_sh",
        "name": "الثانية باكالوريا علوم إنسانية",
        "level": "2BAC",
        "level_num": 3,
        "level_name": "السنة الثانية باكالوريا",
        "category": "الشعب العامة والدولية",
        "subjects": {
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "HG": {
                "code": "HG",
                "name": "التاريخ والجغرافيا",
                "hours": 5,
                "split": "5",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            }
        }
    },
    {
        "id": "2bac_agri",
        "name": "الثانية باكالوريا علوم زراعية",
        "level": "2BAC",
        "level_num": 3,
        "level_name": "السنة الثانية باكالوريا",
        "category": "الشعب العامة والدولية",
        "subjects": {
            "PC": {
                "code": "PC",
                "name": "الفيزياء والكيمياء",
                "hours": 4,
                "split": "4",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "SVT": {
                "code": "SVT",
                "name": "علوم الحياة  والأرض",
                "hours": 6,
                "split": "6",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 5,
                "split": "5",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 1,
                "split": "1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            }
        }
    },
    {
        "id": "2bac_sma",
        "name": "الثانية باكالوريا علوم رياضية أ",
        "level": "2BAC",
        "level_num": 3,
        "level_name": "السنة الثانية باكالوريا",
        "category": "الشعب العامة والدولية",
        "subjects": {
            "PC": {
                "code": "PC",
                "name": "الفيزياء والكيمياء",
                "hours": 6,
                "split": "6",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "SVT": {
                "code": "SVT",
                "name": "علوم الحياة  والأرض",
                "hours": 2,
                "split": "2",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 7,
                "split": "7",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 1,
                "split": "1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            }
        }
    },
    {
        "id": "2bac_smb",
        "name": "الثانية باكالوريا علوم رياضية ب",
        "level": "2BAC",
        "level_num": 3,
        "level_name": "السنة الثانية باكالوريا",
        "category": "الشعب العامة والدولية",
        "subjects": {
            "PC": {
                "code": "PC",
                "name": "الفيزياء والكيمياء",
                "hours": 6,
                "split": "6",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 7,
                "split": "7",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 1,
                "split": "1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            },
            "SI": {
                "code": "SI",
                "name": "علوم المهندس",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة علوم المهندس",
                "is_grouped": false
            }
        }
    },
    {
        "id": "2bac_pc_biof",
        "name": "الثانية باكالوريا علوم فيزيائية - دولي فرنسية",
        "level": "2BAC",
        "level_num": 3,
        "level_name": "السنة الثانية باكالوريا",
        "category": "الشعب العامة والدولية",
        "subjects": {
            "PC": {
                "code": "PC",
                "name": "الفيزياء والكيمياء",
                "hours": 6,
                "split": "2+2G",
                "room_type": "مختبر علمي",
                "is_grouped": true
            },
            "SVT": {
                "code": "SVT",
                "name": "علوم الحياة  والأرض",
                "hours": 4,
                "split": "1+2G",
                "room_type": "مختبر علمي",
                "is_grouped": true
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 5,
                "split": "2+2+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 6,
                "split": "2+2+1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "1+1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 1,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "1+1",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            }
        }
    },
    {
        "id": "2bac_svt_biof",
        "name": "الثانية باكالوريا علوم الحياة والأرض - دولي فرنسية",
        "level": "2BAC",
        "level_num": 3,
        "level_name": "السنة الثانية باكالوريا",
        "category": "الشعب العامة والدولية",
        "subjects": {
            "PC": {
                "code": "PC",
                "name": "الفيزياء والكيمياء",
                "hours": 4,
                "split": "2+2G",
                "room_type": "مختبر علمي",
                "is_grouped": true
            },
            "SVT": {
                "code": "SVT",
                "name": "علوم الحياة  والأرض",
                "hours": 6,
                "split": "1+2G",
                "room_type": "مختبر علمي",
                "is_grouped": true
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 5,
                "split": "2+2+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 6,
                "split": "2+2+1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "1+1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 1,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "1+1",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            }
        }
    },
    {
        "id": "2bac_sma_biof",
        "name": "الثانية باكالوريا علوم رياضية أ - دولي فرنسية",
        "level": "2BAC",
        "level_num": 3,
        "level_name": "السنة الثانية باكالوريا",
        "category": "الشعب العامة والدولية",
        "subjects": {
            "PC": {
                "code": "PC",
                "name": "الفيزياء والكيمياء",
                "hours": 6,
                "split": "2+2G",
                "room_type": "مختبر علمي",
                "is_grouped": true
            },
            "SVT": {
                "code": "SVT",
                "name": "علوم الحياة  والأرض",
                "hours": 2,
                "split": "1+2G",
                "room_type": "مختبر علمي",
                "is_grouped": true
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 7,
                "split": "2+2+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 6,
                "split": "2+2+1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "1+1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 1,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "1+1",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            }
        }
    },
    {
        "id": "2bac_smb_biof",
        "name": "الثانية باكالوريا علوم رياضية ب - دولي فرنسية",
        "level": "2BAC",
        "level_num": 3,
        "level_name": "السنة الثانية باكالوريا",
        "category": "الشعب العامة والدولية",
        "subjects": {
            "PC": {
                "code": "PC",
                "name": "الفيزياء والكيمياء",
                "hours": 6,
                "split": "2+2G",
                "room_type": "مختبر علمي",
                "is_grouped": true
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 7,
                "split": "2+2+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 6,
                "split": "2+2+1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "1+1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 1,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "1+1",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            },
            "SI": {
                "code": "SI",
                "name": "علوم المهندس",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة علوم المهندس",
                "is_grouped": false
            }
        }
    },
    {
        "id": "2bac_l_biof",
        "name": "الثانية باكالوريا آداب - دولي فرنسية",
        "level": "2BAC",
        "level_num": 3,
        "level_name": "السنة الثانية باكالوريا",
        "category": "الشعب العامة والدولية",
        "subjects": {
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 2,
                "split": "2+2+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 5,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 8,
                "split": "2+2+1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 5,
                "split": "1+1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "HG": {
                "code": "HG",
                "name": "التاريخ والجغرافيا",
                "hours": 4,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 2,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 3,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "1+1",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            }
        }
    },
    {
        "id": "2bac_sh_biof",
        "name": "الثانية باكالوريا علوم إنسانية - دولي فرنسية",
        "level": "2BAC",
        "level_num": 3,
        "level_name": "السنة الثانية باكالوريا",
        "category": "الشعب العامة والدولية",
        "subjects": {
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 2,
                "split": "2+2+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 4,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 7,
                "split": "2+2+1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 4,
                "split": "1+1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "HG": {
                "code": "HG",
                "name": "التاريخ والجغرافيا",
                "hours": 5,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 3,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 4,
                "split": "1+1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "1+1",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            }
        }
    },
    {
        "id": "tc_orig",
        "name": "الجذع المشترك للتعليم الأصيل",
        "level": "TC",
        "level_num": 1,
        "level_name": "الجذوع المشتركة",
        "category": "التعليم الأصيل",
        "subjects": {
            "SVT": {
                "code": "SVT",
                "name": "علوم الحياة  والأرض",
                "hours": 1,
                "split": "1",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 5,
                "split": "5",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "HG": {
                "code": "HG",
                "name": "التاريخ والجغرافيا",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 7,
                "split": "7",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            },
            "INF": {
                "code": "INF",
                "name": "المعلوميات",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة الإعلاميات",
                "is_grouped": false
            },
            "FO": {
                "code": "FO",
                "name": "الفقه والأصول",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "TH": {
                "code": "TH",
                "name": "التفسير والحديث",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "DOC": {
                "code": "DOC",
                "name": "التوثيق",
                "hours": 1,
                "split": "1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            }
        }
    },
    {
        "id": "1bac_shar",
        "name": "الأولى باكالوريا علوم شرعية",
        "level": "1BAC",
        "level_num": 2,
        "level_name": "السنة الأولى باكالوريا",
        "category": "التعليم الأصيل",
        "subjects": {
            "SVT": {
                "code": "SVT",
                "name": "علوم الحياة  والأرض",
                "hours": 1,
                "split": "1",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 5,
                "split": "5",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "HG": {
                "code": "HG",
                "name": "التاريخ والجغرافيا",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 11,
                "split": "11",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            },
            "FO": {
                "code": "FO",
                "name": "الفقه والأصول",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "TH": {
                "code": "TH",
                "name": "التفسير والحديث",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "DOC": {
                "code": "DOC",
                "name": "التوثيق",
                "hours": 1,
                "split": "1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "FT": {
                "code": "FT",
                "name": "الفرائض والتوقيت",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            }
        }
    },
    {
        "id": "1bac_lar",
        "name": "الأولى باكالوريا لغة عربية",
        "level": "1BAC",
        "level_num": 2,
        "level_name": "السنة الأولى باكالوريا",
        "category": "التعليم الأصيل",
        "subjects": {
            "SVT": {
                "code": "SVT",
                "name": "علوم الحياة  والأرض",
                "hours": 1,
                "split": "1",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 7,
                "split": "7",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "HG": {
                "code": "HG",
                "name": "التاريخ والجغرافيا",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 5,
                "split": "5",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            },
            "TH": {
                "code": "TH",
                "name": "التفسير والحديث",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "DOC": {
                "code": "DOC",
                "name": "التوثيق",
                "hours": 1,
                "split": "1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            }
        }
    },
    {
        "id": "2bac_shar",
        "name": "الثانية باكالوريا علوم شرعية",
        "level": "2BAC",
        "level_num": 3,
        "level_name": "السنة الثانية باكالوريا",
        "category": "التعليم الأصيل",
        "subjects": {
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 5,
                "split": "5",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "HG": {
                "code": "HG",
                "name": "التاريخ والجغرافيا",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 11,
                "split": "11",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            },
            "FO": {
                "code": "FO",
                "name": "الفقه والأصول",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "TH": {
                "code": "TH",
                "name": "التفسير والحديث",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "DOC": {
                "code": "DOC",
                "name": "التوثيق",
                "hours": 1,
                "split": "1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "FT": {
                "code": "FT",
                "name": "الفرائض والتوقيت",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            }
        }
    },
    {
        "id": "2bac_lar",
        "name": "الثانية باكالوريا لغة عربية",
        "level": "2BAC",
        "level_num": 3,
        "level_name": "السنة الثانية باكالوريا",
        "category": "التعليم الأصيل",
        "subjects": {
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 7,
                "split": "7",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "HG": {
                "code": "HG",
                "name": "التاريخ والجغرافيا",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 5,
                "split": "5",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            },
            "TH": {
                "code": "TH",
                "name": "التفسير والحديث",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "DOC": {
                "code": "DOC",
                "name": "التوثيق",
                "hours": 1,
                "split": "1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            }
        }
    },
    {
        "id": "tc_tech",
        "name": "الجذع المشترك التكنولوجي",
        "level": "TC",
        "level_num": 1,
        "level_name": "الجذوع المشتركة",
        "category": "الشعب التقنية والاقتصادية",
        "subjects": {
            "PC": {
                "code": "PC",
                "name": "الفيزياء والكيمياء",
                "hours": 4,
                "split": "4",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 5,
                "split": "5",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "HG": {
                "code": "HG",
                "name": "التاريخ والجغرافيا",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            },
            "INF": {
                "code": "INF",
                "name": "المعلوميات",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة الإعلاميات",
                "is_grouped": false
            },
            "SI": {
                "code": "SI",
                "name": "علوم المهندس",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة علوم المهندس",
                "is_grouped": false
            }
        }
    },
    {
        "id": "1bac_ste",
        "name": "الأولى باكالوريا علوم وتكنولوجيات كهربائية",
        "level": "1BAC",
        "level_num": 2,
        "level_name": "السنة الأولى باكالوريا",
        "category": "الشعب التقنية والاقتصادية",
        "subjects": {
            "PC": {
                "code": "PC",
                "name": "الفيزياء والكيمياء",
                "hours": 4,
                "split": "4",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 5,
                "split": "5",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            },
            "SI": {
                "code": "SI",
                "name": "علوم المهندس",
                "hours": 9,
                "split": "9",
                "room_type": "قاعة علوم المهندس",
                "is_grouped": false
            }
        }
    },
    {
        "id": "1bac_stm",
        "name": "الأولى باكالوريا علوم وتكنولوجيات ميكانيكية",
        "level": "1BAC",
        "level_num": 2,
        "level_name": "السنة الأولى باكالوريا",
        "category": "الشعب التقنية والاقتصادية",
        "subjects": {
            "PC": {
                "code": "PC",
                "name": "الفيزياء والكيمياء",
                "hours": 4,
                "split": "4",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 5,
                "split": "5",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            },
            "SI": {
                "code": "SI",
                "name": "علوم المهندس",
                "hours": 9,
                "split": "9",
                "room_type": "قاعة علوم المهندس",
                "is_grouped": false
            }
        }
    },
    {
        "id": "2bac_ste",
        "name": "الثانية باكالوريا علوم وتكنولوجيات كهربائية",
        "level": "2BAC",
        "level_num": 3,
        "level_name": "السنة الثانية باكالوريا",
        "category": "الشعب التقنية والاقتصادية",
        "subjects": {
            "PC": {
                "code": "PC",
                "name": "الفيزياء والكيمياء",
                "hours": 4,
                "split": "4",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 5,
                "split": "5",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 1,
                "split": "1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            },
            "SI": {
                "code": "SI",
                "name": "علوم المهندس",
                "hours": 9,
                "split": "9",
                "room_type": "قاعة علوم المهندس",
                "is_grouped": false
            }
        }
    },
    {
        "id": "2bac_stm",
        "name": "الثانية باكالوريا علوم وتكنولوجيات ميكانيكية",
        "level": "2BAC",
        "level_num": 3,
        "level_name": "السنة الثانية باكالوريا",
        "category": "الشعب التقنية والاقتصادية",
        "subjects": {
            "PC": {
                "code": "PC",
                "name": "الفيزياء والكيمياء",
                "hours": 4,
                "split": "4",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 5,
                "split": "5",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 1,
                "split": "1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            },
            "SI": {
                "code": "SI",
                "name": "علوم المهندس",
                "hours": 9,
                "split": "9",
                "room_type": "قاعة علوم المهندس",
                "is_grouped": false
            }
        }
    },
    {
        "id": "1bac_seg",
        "name": "الأولى باكالوريا علوم اقتصادية وتدبير",
        "level": "1BAC",
        "level_num": 2,
        "level_name": "السنة الأولى باكالوريا",
        "category": "الشعب التقنية والاقتصادية",
        "subjects": {
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "HG": {
                "code": "HG",
                "name": "التاريخ والجغرافيا",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            },
            "COMP": {
                "code": "COMP",
                "name": "المحاسبة",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EGS": {
                "code": "EGS",
                "name": "الاقتصاد العام والاحصاء",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ORG": {
                "code": "ORG",
                "name": "الاقتصاد والتنظيم الإداري للمقاولات",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "DR": {
                "code": "DR",
                "name": "القانون",
                "hours": 1,
                "split": "1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "IG": {
                "code": "IG",
                "name": "معلوميات التدبير",
                "hours": 1,
                "split": "1",
                "room_type": "قاعة الإعلاميات",
                "is_grouped": false
            }
        }
    },
    {
        "id": "2bac_eco",
        "name": "الثانية باكالوريا علوم اقتصادية",
        "level": "2BAC",
        "level_num": 3,
        "level_name": "السنة الثانية باكالوريا",
        "category": "الشعب التقنية والاقتصادية",
        "subjects": {
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "HG": {
                "code": "HG",
                "name": "التاريخ والجغرافيا",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 1,
                "split": "1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            },
            "COMP": {
                "code": "COMP",
                "name": "المحاسبة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EGS": {
                "code": "EGS",
                "name": "الاقتصاد العام والاحصاء",
                "hours": 6,
                "split": "6",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ORG": {
                "code": "ORG",
                "name": "الاقتصاد والتنظيم الإداري للمقاولات",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "DR": {
                "code": "DR",
                "name": "القانون",
                "hours": 1,
                "split": "1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "IG": {
                "code": "IG",
                "name": "معلوميات التدبير",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة الإعلاميات",
                "is_grouped": false
            }
        }
    },
    {
        "id": "2bac_sgc",
        "name": "الثانية باكالوريا علوم التدبير المحاسباتي",
        "level": "2BAC",
        "level_num": 3,
        "level_name": "السنة الثانية باكالوريا",
        "category": "الشعب التقنية والاقتصادية",
        "subjects": {
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "HG": {
                "code": "HG",
                "name": "التاريخ والجغرافيا",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 1,
                "split": "1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            },
            "COMP": {
                "code": "COMP",
                "name": "المحاسبة",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EGS": {
                "code": "EGS",
                "name": "الاقتصاد العام والاحصاء",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ORG": {
                "code": "ORG",
                "name": "الاقتصاد والتنظيم الإداري للمقاولات",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "DR": {
                "code": "DR",
                "name": "القانون",
                "hours": 1,
                "split": "1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "IG": {
                "code": "IG",
                "name": "معلوميات التدبير",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة الإعلاميات",
                "is_grouped": false
            }
        }
    },
    {
        "id": "1bac_ap",
        "name": "الأولى باكالوريا فنون تطبيقية",
        "level": "1BAC",
        "level_num": 2,
        "level_name": "السنة الأولى باكالوريا",
        "category": "الشعب التقنية والاقتصادية",
        "subjects": {
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            },
            "IINF": {
                "code": "IINF",
                "name": "المعلوميات والانفوغرافيا",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة الإعلاميات",
                "is_grouped": false
            },
            "DEP": {
                "code": "DEP",
                "name": "الرسم والتعبير التشكيلي",
                "hours": 4,
                "split": "4",
                "room_type": "ورشة الفنون التطبيقية",
                "is_grouped": false
            },
            "CPHA": {
                "code": "CPHA",
                "name": "الثقافة التشكيلية وتاريخ الفن",
                "hours": 3,
                "split": "3",
                "room_type": "ورشة الفنون التطبيقية",
                "is_grouped": false
            },
            "AG": {
                "code": "AG",
                "name": "فنون الغرافيك",
                "hours": 4,
                "split": "4",
                "room_type": "ورشة الفنون التطبيقية",
                "is_grouped": false
            },
            "V": {
                "code": "V",
                "name": "الحجم",
                "hours": 4,
                "split": "4",
                "room_type": "ورشة الفنون التطبيقية",
                "is_grouped": false
            }
        }
    },
    {
        "id": "2bac_ap",
        "name": "الثانية باكالوريا فنون تطبيقية",
        "level": "2BAC",
        "level_num": 3,
        "level_name": "السنة الثانية باكالوريا",
        "category": "الشعب التقنية والاقتصادية",
        "subjects": {
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 1,
                "split": "1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            },
            "IINF": {
                "code": "IINF",
                "name": "المعلوميات والانفوغرافيا",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة الإعلاميات",
                "is_grouped": false
            },
            "CPHA": {
                "code": "CPHA",
                "name": "الثقافة التشكيلية وتاريخ الفن",
                "hours": 2,
                "split": "2",
                "room_type": "ورشة الفنون التطبيقية",
                "is_grouped": false
            },
            "COM": {
                "code": "COM",
                "name": "تصميم التواصل",
                "hours": 6,
                "split": "6",
                "room_type": "ورشة الفنون التطبيقية",
                "is_grouped": false
            },
            "ENV": {
                "code": "ENV",
                "name": "تصميم المحيط",
                "hours": 3,
                "split": "3",
                "room_type": "ورشة الفنون التطبيقية",
                "is_grouped": false
            },
            "PROD": {
                "code": "PROD",
                "name": "تصميم المنتوج",
                "hours": 3,
                "split": "3",
                "room_type": "ورشة الفنون التطبيقية",
                "is_grouped": false
            }
        }
    },
    {
        "id": "tc_pro_serv",
        "name": "الجذع المشترك المهني - خدماتي",
        "level": "TC",
        "level_num": 1,
        "level_name": "الجذوع المشتركة",
        "category": "بكالوريا مهنية",
        "subjects": {
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 5,
                "split": "5",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "HG": {
                "code": "HG",
                "name": "التاريخ والجغرافيا",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            },
            "INF": {
                "code": "INF",
                "name": "المعلوميات",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة الإعلاميات",
                "is_grouped": false
            }
        }
    },
    {
        "id": "tc_pro_ind",
        "name": "الجذع المشترك المهني - صناعي",
        "level": "TC",
        "level_num": 1,
        "level_name": "الجذوع المشتركة",
        "category": "بكالوريا مهنية",
        "subjects": {
            "PC": {
                "code": "PC",
                "name": "الفيزياء والكيمياء",
                "hours": 4,
                "split": "4",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 5,
                "split": "5",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "HG": {
                "code": "HG",
                "name": "التاريخ والجغرافيا",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            },
            "INF": {
                "code": "INF",
                "name": "المعلوميات",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة الإعلاميات",
                "is_grouped": false
            }
        }
    },
    {
        "id": "tc_pro_agri",
        "name": "الجذع المشترك المهني - فلاحي",
        "level": "TC",
        "level_num": 1,
        "level_name": "الجذوع المشتركة",
        "category": "بكالوريا مهنية",
        "subjects": {
            "PC": {
                "code": "PC",
                "name": "الفيزياء والكيمياء",
                "hours": 4,
                "split": "4",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "SVT": {
                "code": "SVT",
                "name": "علوم الحياة  والأرض",
                "hours": 3,
                "split": "3",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 5,
                "split": "5",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "HG": {
                "code": "HG",
                "name": "التاريخ والجغرافيا",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            },
            "INF": {
                "code": "INF",
                "name": "المعلوميات",
                "hours": 1,
                "split": "1",
                "room_type": "قاعة الإعلاميات",
                "is_grouped": false
            }
        }
    },
    {
        "id": "st_185",
        "name": "الأولى باكالوريا - شعبة الخدمات: التجارة - المحاسبة - التسيير والإدارة - تصميم الأزياء",
        "level": "1BAC",
        "level_num": 2,
        "level_name": "السنة الأولى باكالوريا",
        "category": "بكالوريا مهنية",
        "subjects": {
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            }
        }
    },
    {
        "id": "st_186",
        "name": "الأولى باكالوريا - شعبة الخدمات: فنون الطبخ  - خدمات الطعامة - الاستقبال الفندقي - اللوجيستيك",
        "level": "1BAC",
        "level_num": 2,
        "level_name": "السنة الأولى باكالوريا",
        "category": "بكالوريا مهنية",
        "subjects": {
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            }
        }
    },
    {
        "id": "st_187",
        "name": "الأولى باكالوريا - الشعب الصناعية",
        "level": "1BAC",
        "level_num": 2,
        "level_name": "السنة الأولى باكالوريا",
        "category": "بكالوريا مهنية",
        "subjects": {
            "PC": {
                "code": "PC",
                "name": "الفيزياء والكيمياء",
                "hours": 3,
                "split": "3",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            }
        }
    },
    {
        "id": "st_188",
        "name": "الأولى باكالوريا - شعبة الفلاحة",
        "level": "1BAC",
        "level_num": 2,
        "level_name": "السنة الأولى باكالوريا",
        "category": "بكالوريا مهنية",
        "subjects": {
            "PC": {
                "code": "PC",
                "name": "الفيزياء والكيمياء",
                "hours": 3,
                "split": "3",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "SVT": {
                "code": "SVT",
                "name": "علوم الحياة  والأرض",
                "hours": 3,
                "split": "3",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            }
        }
    },
    {
        "id": "st_189",
        "name": "الثانية باكالوريا - شعبة الخدمات: التجارة - المحاسبة - التسيير والإدارة - تصميم الأزياء",
        "level": "2BAC",
        "level_num": 3,
        "level_name": "السنة الثانية باكالوريا",
        "category": "بكالوريا مهنية",
        "subjects": {
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 1,
                "split": "1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            }
        }
    },
    {
        "id": "st_190",
        "name": "الثانية باكالوريا - شعبة الخدمات: فنون الطبخ  - خدمات الطعامة - الاستقبال الفندقي - اللوجيستيك",
        "level": "2BAC",
        "level_num": 3,
        "level_name": "السنة الثانية باكالوريا",
        "category": "بكالوريا مهنية",
        "subjects": {
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 1,
                "split": "1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            }
        }
    },
    {
        "id": "st_191",
        "name": "الثانية باكالوريا - الشعب الصناعية",
        "level": "2BAC",
        "level_num": 3,
        "level_name": "السنة الثانية باكالوريا",
        "category": "بكالوريا مهنية",
        "subjects": {
            "PC": {
                "code": "PC",
                "name": "الفيزياء والكيمياء",
                "hours": 3,
                "split": "3",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 1,
                "split": "1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            }
        }
    },
    {
        "id": "st_192",
        "name": "الثانية باكالوريا - شعبة الفلاحة",
        "level": "2BAC",
        "level_num": 3,
        "level_name": "السنة الثانية باكالوريا",
        "category": "بكالوريا مهنية",
        "subjects": {
            "PC": {
                "code": "PC",
                "name": "الفيزياء والكيمياء",
                "hours": 3,
                "split": "3",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "SVT": {
                "code": "SVT",
                "name": "علوم الحياة  والأرض",
                "hours": 3,
                "split": "3",
                "room_type": "مختبر علمي",
                "is_grouped": false
            },
            "M": {
                "code": "M",
                "name": "الرياضيات",
                "hours": 4,
                "split": "4",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "A": {
                "code": "A",
                "name": "اللغة  العربية",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "F": {
                "code": "F",
                "name": "اللغة  الفرنسية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "ENG": {
                "code": "ENG",
                "name": "اللغة الإنجليزية",
                "hours": 3,
                "split": "3",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "I": {
                "code": "I",
                "name": "التربية الإسلامية",
                "hours": 1,
                "split": "1",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "PH": {
                "code": "PH",
                "name": "الفلسفة",
                "hours": 2,
                "split": "2",
                "room_type": "قاعة عامة",
                "is_grouped": false
            },
            "EPS": {
                "code": "EPS",
                "name": "التربية البدنية والرياضة",
                "hours": 2,
                "split": "2",
                "room_type": "فضاء رياضي",
                "is_grouped": false
            }
        }
    }
]

# Ministerial Non-Generalized Subjects Allocation Maps (Official Ministerial Norms)
# Informatics (المعلوميات): 2h in TC (1h in tc_pro_agri), 0h elsewhere
INF_STREAM_HOURS = {
    "tc_sc": 2,
    "tc_sc_biof": 2,
    "tc_lsh": 2,
    "tc_lsh_biof": 2,
    "tc_orig": 2,
    "tc_tech": 2,
    "tc_pro_serv": 2,
    "tc_pro_ind": 2,
    "tc_pro_agri": 1,
}

# Translation (الترجمة): 2h in standard non-BIOF scientific/math baccalaureate streams, 0h elsewhere
TR_STREAM_HOURS = {
    "1bac_exp": 2,
    "1bac_sm": 2,
    "2bac_pc": 2,
    "2bac_svt": 2,
    "2bac_agri": 2,
    "2bac_sma": 2,
    "2bac_smb": 2,
}

class HighSchoolCurriculumEngine:
    def __init__(self):
        self.streams = HIGH_SCHOOL_STREAMS
        self.subjects_catalog = HIGH_SCHOOL_SUBJECTS
        self.non_generalized_configs = [
            {
                "name": "المعلوميات",
                "code": "INF",
                "is_active": True,
                "room_type": "قاعة الإعلاميات المتعددة الوسائط",
                "description": "2 س بالجذوع المشتركة (1 س بالفلاحي)"
            },
            {
                "name": "الترجمة",
                "code": "TR",
                "is_active": True,
                "room_type": "قاعة عامة",
                "description": "2 س بمسالك البكالوريا العلمية والرياضية العادية"
            }
        ]

    def is_subject_active(self, subj_code_or_name: str) -> bool:
        clean = (subj_code_or_name or "").strip()
        for cfg in self.non_generalized_configs:
            if cfg["code"] == clean or cfg["name"] == clean or clean in cfg["name"] or cfg["name"] in clean:
                return cfg["is_active"]
        return True

    def toggle_non_generalized(self, subj_name_or_code: str) -> bool:
        clean = (subj_name_or_code or "").strip()
        for cfg in self.non_generalized_configs:
            if cfg["code"] == clean or cfg["name"] == clean or clean in cfg["name"] or cfg["name"] in clean:
                cfg["is_active"] = not cfg["is_active"]
                return cfg["is_active"]
        return False

    def get_stream_subjects(self, stream: Dict[str, Any]) -> Dict[str, Any]:
        s_id = stream.get("id", "")
        base_subjects = stream.get("subjects", {})
        result = {}
        for scode, sinfo in base_subjects.items():
            s_name = sinfo.get("name", "")
            if scode == "INF" or "معلوميات" in s_name:
                if not self.is_subject_active("INF"):
                    continue
            if scode == "TR" or "ترجمة" in s_name:
                if not self.is_subject_active("TR"):
                    continue
            result[scode] = dict(sinfo)

        # Inject INF if active and stream is in INF_STREAM_HOURS
        s_id_norm = s_id.lower()
        if self.is_subject_active("INF") and (s_id_norm in INF_STREAM_HOURS or s_id_norm.replace("_f", "_biof") in INF_STREAM_HOURS):
            h = INF_STREAM_HOURS.get(s_id_norm, INF_STREAM_HOURS.get(s_id_norm.replace("_f", "_biof"), 2))
            if "INF" not in result:
                result["INF"] = {
                    "code": "INF",
                    "name": "المعلوميات",
                    "hours": h,
                    "split": str(h),
                    "room_type": "قاعة الإعلاميات المتعددة الوسائط",
                    "is_grouped": False
                }
            else:
                result["INF"]["hours"] = h
                result["INF"]["split"] = str(h)

        # Inject TR if active and stream is in TR_STREAM_HOURS
        if self.is_subject_active("TR") and (s_id_norm in TR_STREAM_HOURS or s_id_norm.replace("_f", "_biof") in TR_STREAM_HOURS):
            h = TR_STREAM_HOURS.get(s_id_norm, TR_STREAM_HOURS.get(s_id_norm.replace("_f", "_biof"), 2))
            if "TR" not in result:
                result["TR"] = {
                    "code": "TR",
                    "name": "الترجمة",
                    "hours": h,
                    "split": str(h),
                    "room_type": "قاعة عامة",
                    "is_grouped": False
                }
            else:
                result["TR"]["hours"] = h
                result["TR"]["split"] = str(h)

        return result

    def get_all_streams(self) -> List[Dict[str, Any]]:
        return self.streams

    def get_stream_by_id(self, stream_id: str) -> Dict[str, Any]:
        for s in self.streams:
            if s["id"] == stream_id:
                return s
        return None

    def register_custom_stream(self, stream_dict: Dict[str, Any]):
        if not hasattr(self, 'streams') or not isinstance(self.streams, list):
            self.streams = list(HIGH_SCHOOL_STREAMS)
        for idx, s in enumerate(self.streams):
            if s["id"] == stream_dict["id"]:
                self.streams[idx] = stream_dict
                return
        self.streams.append(stream_dict)

    def calculate_quotas(self, stream_counts: Dict[str, int]) -> Dict[str, Any]:
        """
        Calculates total hours per subject, required teachers (based on 21h/week),
        and required rooms (based on 48h capacity) for High School.
        """
        subject_totals = {}
        for s_code, s_name in self.subjects_catalog.items():
            subject_totals[s_code] = {
                "code": s_code,
                "name": s_name,
                "hours_tc": 0,
                "hours_1bac": 0,
                "hours_2bac": 0,
                "total_hours": 0,
                "room_type": "قاعة عامة",
                "required_teachers": 0,
                "required_rooms": 0
            }

        total_classes_count = 0
        classes_by_level = {"TC": 0, "1BAC": 0, "2BAC": 0}

        for stream in self.streams:
            s_id = stream["id"]
            cnt = int(stream_counts.get(s_id, 0))
            if cnt <= 0:
                continue

            lvl = stream["level"]
            classes_by_level[lvl] += cnt
            total_classes_count += cnt

            stream_subjs = self.get_stream_subjects(stream)
            for scode, sinfo in stream_subjs.items():
                if scode not in subject_totals:
                    subject_totals[scode] = {
                        "code": scode,
                        "name": sinfo["name"],
                        "hours_tc": 0,
                        "hours_1bac": 0,
                        "hours_2bac": 0,
                        "total_hours": 0,
                        "room_type": sinfo.get("room_type", "قاعة عامة"),
                        "required_teachers": 0,
                        "required_rooms": 0
                    }
                
                h = sinfo["hours"] * cnt
                if lvl == "TC":
                    subject_totals[scode]["hours_tc"] += h
                elif lvl == "1BAC":
                    subject_totals[scode]["hours_1bac"] += h
                elif lvl == "2BAC":
                    subject_totals[scode]["hours_2bac"] += h

                subject_totals[scode]["total_hours"] += h
                subject_totals[scode]["room_type"] = sinfo.get("room_type", "قاعة عامة")

        # Quota calculations: 21h for high school teachers!
        active_quotas = []
        for scode, data in subject_totals.items():
            tot = data["total_hours"]
            if tot > 0:
                data["required_teachers"] = math.ceil(tot / 21.0)
                data["required_rooms"] = math.ceil(tot / 48.0)
                active_quotas.append(data)

        # Sort by total hours descending
        active_quotas.sort(key=lambda x: x["total_hours"], reverse=True)

        return {
            "total_classes": total_classes_count,
            "classes_by_level": classes_by_level,
            "quotas": active_quotas
        }

    def generate_classes_list(self, stream_counts: Dict[str, int]) -> List[Dict[str, Any]]:
        """
        Generates individual class entries like TC-SC-1, 1BAC-LSH-F-1, etc.
        Replaces -BIOF with -F in class codes as per ministerial naming conventions.
        """
        classes = []
        for stream in self.streams:
            s_id = stream["id"]
            cnt = int(stream_counts.get(s_id, 0))
            if cnt <= 0:
                continue
            
            # Short code for FET class naming (e.g. 1BAC-LSH-F-1 instead of 1BAC-LSH-BIOF-1)
            code_prefix = s_id.upper().replace("_", "-").replace("-BIOF", "-F")
            stream_subjs = self.get_stream_subjects(stream)
            for i in range(1, cnt + 1):
                class_code = f"{code_prefix}-{i}"
                class_label = f"{stream['name']} {i}"
                classes.append({
                    "code": class_code,
                    "label": class_label,
                    "stream_id": s_id,
                    "stream_name": stream["name"],
                    "level": stream["level_num"],
                    "level_code": stream["level"],
                    "level_label": stream["level_name"],
                    "category": stream["category"],
                    "subjects": stream_subjs
                })
        return classes

    def _distribute_high_school_subject(self, items: List[Any], num_teachers: int) -> List[List[Any]]:
        if num_teachers <= 1:
            return [list(items)]
        total_hours = sum(it[1] for it in items)
        target_cap = max(21, math.ceil(total_hours / num_teachers))
        target_avg = total_hours / float(num_teachers)
        sorted_items = sorted(items, key=lambda x: (-x[1], x[2], x[0]))
        buckets = [[] for _ in range(num_teachers)]
        for item in sorted_items:
            best_t = -1
            best_score = float('inf')
            for t in range(num_teachers):
                ch = sum(x[1] for x in buckets[t])
                if ch + item[1] <= target_cap:
                    levels = set(x[2] for x in buckets[t])
                    lvl_pen = -10 if item[2] in levels else (25 if len(levels) >= 2 else 0)
                    score = (abs(ch + item[1] - target_avg) * 50) + (ch * 10) + lvl_pen
                else:
                    score = 10000 + (ch + item[1] - target_cap) * 100
                if score < best_score:
                    best_score = score
                    best_t = t
            buckets[best_t].append(item)

        # Balancing pass: equalize teacher hours without exceeding target_cap
        improved = True
        while improved:
            improved = False
            h_list = [sum(x[1] for x in b) for b in buckets]
            max_t = h_list.index(max(h_list))
            min_t = h_list.index(min(h_list))
            cur_gap = h_list[max_t] - h_list[min_t]
            if cur_gap <= 2:
                break
            for i, it in enumerate(buckets[max_t]):
                new_gap = abs((h_list[max_t] - it[1]) - (h_list[min_t] + it[1]))
                if new_gap < cur_gap and (h_list[min_t] + it[1] <= target_cap):
                    buckets[min_t].append(buckets[max_t].pop(i))
                    improved = True
                    break

        buckets.sort(key=lambda b: (-sum(x[1] for x in b), -len(b)))
        return buckets

    def calculate_assignments(
        self,
        stream_counts: Dict[str, int],
        teacher_counts_by_subject: Dict[str, int] = None,
        teacher_custom_names: Dict[str, str] = None
    ) -> List[Any]:
        """
        Calculates high school assignments based on 21h/week statutory quota (المذكرة 43)
        """
        try:
            from .models import TeacherAssignment
        except (ImportError, ValueError):
            from models import TeacherAssignment

        teacher_counts_by_subject = teacher_counts_by_subject or {}
        teacher_custom_names = teacher_custom_names or {}

        classes = self.generate_classes_list(stream_counts)
        if not classes:
            return []

        def get_user_teacher_count(subj_name: str, def_cnt: int) -> int:
            if subj_name in teacher_counts_by_subject:
                return teacher_counts_by_subject[subj_name]
            clean_s = " ".join(subj_name.split())
            for k, v in teacher_counts_by_subject.items():
                if " ".join(k.split()) == clean_s:
                    return v
            if "بدنية" in clean_s:
                for k in ["التربية البدنية والرياضة", "التربية البدنية"]:
                    if k in teacher_counts_by_subject:
                        return teacher_counts_by_subject[k]
            if "فيزياء" in clean_s:
                for k in ["الفيزياء والكيمياء", "الكيمياء و الفيزياء"]:
                    if k in teacher_counts_by_subject:
                        return teacher_counts_by_subject[k]
            if "حياة" in clean_s:
                for k in ["علوم الحياة  والأرض", "علوم الحياة والأرض", "علوم الحياة و الأرض"]:
                    if k in teacher_counts_by_subject:
                        return teacher_counts_by_subject[k]
            return def_cnt

        subject_items: Dict[str, List[Any]] = {}
        for c in classes:
            c_code = c["code"]
            c_lvl = c["level"]
            for scode, sinfo in c["subjects"].items():
                s_name = sinfo["name"].strip()
                s_hours = sinfo.get("hours", 0)
                if s_hours <= 0:
                    continue
                subject_items.setdefault(s_name, []).append((c_code, s_hours, c_lvl))

        assignments: List[TeacherAssignment] = []
        row_id = 1

        standard_subj_order = [
            "اللغة  العربية", "اللغة العربية",
            "اللغة  الفرنسية", "اللغة الفرنسية",
            "اللغة الإنجليزية",
            "الرياضيات",
            "الفيزياء والكيمياء", "الكيمياء و الفيزياء",
            "علوم الحياة  والأرض", "علوم الحياة والأرض",
            "التاريخ والجغرافيا", "الاجتماعيات",
            "الفلسفة",
            "التربية الإسلامية",
            "التربية البدنية والرياضة", "التربية البدنية",
            "المعلوميات",
            "الترجمة",
            "علوم المهندس",
            "الاقتصاد العام والاحصاء",
            "المحاسبة",
            "الاقتصاد والتنظيم الإداري للمقاولات",
            "القانون",
            "معلوميات التدبير",
            "الرسم والتعبير التشكيلي",
            "الفقه والأصول",
            "التفسير والحديث",
            "الفرائض والتوقيت",
            "التوثيق"
        ]

        ordered_subjects = []
        for s in standard_subj_order:
            if s in subject_items and s not in ordered_subjects:
                ordered_subjects.append(s)
        for s in sorted(subject_items.keys()):
            if s not in ordered_subjects:
                ordered_subjects.append(s)

        for s_name in ordered_subjects:
            items = subject_items.get(s_name, [])
            if not items:
                continue

            total_hours = sum(it[1] for it in items)
            req_teachers = math.ceil(total_hours / 21.0)
            num_teachers = get_user_teacher_count(s_name, req_teachers)
            if num_teachers <= 0:
                num_teachers = req_teachers
            if num_teachers <= 0:
                continue

            allocations = self._distribute_high_school_subject(items, num_teachers)
            avail_levels_for_subj = set(it[2] for it in items)

            for t_idx, t_items in enumerate(allocations):
                if not t_items:
                    continue

                def_name = f"أستاذ {s_name} {t_idx + 1}"
                real_name = (teacher_custom_names.get(def_name) or "").strip()
                teacher_name = real_name if real_name else def_name

                t_items_sorted = sorted(t_items, key=lambda x: (x[2], x[0]))
                assigned_classes = [it[0] for it in t_items_sorted]
                tot_h = sum(it[1] for it in t_items)
                c1_cnt = len([it for it in t_items if it[2] == 1])
                c2_cnt = len([it for it in t_items if it[2] == 2])
                c3_cnt = len([it for it in t_items if it[2] == 3])
                levels = (1 if c1_cnt else 0) + (1 if c2_cnt else 0) + (1 if c3_cnt else 0)

                two_levels_ok = (levels >= 2) or (len(avail_levels_for_subj) <= 1)

                if tot_h == 21:
                    status = "نصاب كامل (21س)"
                elif tot_h < 21:
                    status = f"نصاب مخفف ({tot_h}س)"
                else:
                    status = f"ساعات إضافية ({tot_h}س)"

                assignments.append(TeacherAssignment(
                    row_id=row_id,
                    subject=s_name,
                    teacher_name=teacher_name,
                    classes_1=c1_cnt,
                    classes_2=c2_cnt,
                    classes_3=c3_cnt,
                    assigned_classes_str="، ".join(assigned_classes),
                    total_classes=len(assigned_classes),
                    levels_count=levels,
                    two_levels_satisfied=two_levels_ok,
                    total_hours=tot_h,
                    status_note=status,
                    def_teacher_name=def_name
                ))
                row_id += 1

        return assignments

high_school_engine = HighSchoolCurriculumEngine()

