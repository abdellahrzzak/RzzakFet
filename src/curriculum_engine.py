# -*- coding: utf-8 -*-
import math
from typing import List, Dict, Tuple
from .models import (
    InstitutionData, EducationalStructure, NonGeneralizedSubjectConfig,
    SubjectQuotaCalc, TeacherAssignment
)

class CurriculumEngine:
    def __init__(self, institution: InstitutionData = None, structure: EducationalStructure = None):
        self.institution = institution or InstitutionData()
        self.structure = structure or EducationalStructure()
        
        self.non_generalized_configs = [
            NonGeneralizedSubjectConfig("التكنولوجيا الصناعية", False, 0, 0, 2, "مختبر التكنولوجيا"),
            NonGeneralizedSubjectConfig("التربية الأسرية", False, 0, 2, 0, "ورشة التربية الأسرية"),
            NonGeneralizedSubjectConfig("المعلوميات", True, 0, 1, 1, "قاعة الإعلاميات المتعددة الوسائط"),
            NonGeneralizedSubjectConfig("التربية التشكيلية / أو الموسيقية", False, 2, 2, 2, "مرسم التربية التشكيلية"),
            NonGeneralizedSubjectConfig("اللغة الأجنبية الثانية (الإنجليزية)", True, 0, 0, 2, "قاعة عامة"),
        ]

    def get_subject_quotas(self) -> List[SubjectQuotaCalc]:
        n1 = self.structure.classes_1_apic
        n2 = self.structure.classes_2_apic
        n3 = self.structure.classes_3_apic

        splits_cfg = getattr(self.institution, 'subject_split_modes', {}) or {}

        def _resolve_subject_hours(subject_name, def_h1, def_h2, def_h3):
            cfg = None
            for sk, sv in splits_cfg.items():
                if sk == subject_name or (sk in subject_name) or (subject_name in sk):
                    cfg = sv
                    break
            if not cfg:
                return def_h1, def_h2, def_h3

            def parse_mode_val(val, default):
                if not val:
                    return default
                val_str = str(val).strip()
                if "+" in val_str:
                    parts = [int(p.strip()) for p in val_str.split("+") if p.strip().isdigit()]
                    return sum(parts) if parts else default
                elif val_str.isdigit():
                    return int(val_str)
                return default

            h1 = parse_mode_val(cfg.get("mode_l1", cfg.get("mode")), def_h1)
            h2 = parse_mode_val(cfg.get("mode_l2", cfg.get("mode")), def_h2)
            h3 = parse_mode_val(cfg.get("mode_l3", cfg.get("mode")), def_h3)
            return h1, h2, h3

        base_subjects = [
            ("التربية الإسلامية", True, 2, 2, 2),
            ("اللغة العربية", True, 4, 4, 4),
            ("الاجتماعيات", True, 3, 3, 3),
            ("الرياضيات", True, 5, 4, 5),
            ("علوم الحياة و الأرض", True, 2, 2, 3),
            ("الكيمياء و الفيزياء", True, 2, 2, 3),
            ("اللغة الأجنبية الأولى (الفرنسية)", True, 4, 4, 4),
            ("التربية البدنية", True, 2, 2, 2),
        ]

        results = []
        for name, is_gen, d_h1, d_h2, d_h3 in base_subjects:
            h1, h2, h3 = _resolve_subject_hours(name, d_h1, d_h2, d_h3)
            tot_h1 = n1 * h1
            tot_h2 = n2 * h2
            tot_h3 = n3 * h3
            tot_h = tot_h1 + tot_h2 + tot_h3
            req_rooms = math.ceil(tot_h / 48.0) if tot_h > 0 else 0
            req_teachers = math.ceil(tot_h / 24.0) if tot_h > 0 else 0
            results.append(SubjectQuotaCalc(
                name=name, is_generalized=True,
                hours_1=h1, hours_2=h2, hours_3=h3,
                total_hours=tot_h, required_rooms=req_rooms, required_teachers=req_teachers,
                hours_level_1=tot_h1, hours_level_2=tot_h2, hours_level_3=tot_h3
            ))

        for cfg in self.non_generalized_configs:
            h1 = cfg.hours_1_apic if cfg.is_active else 0
            h2 = cfg.hours_2_apic if cfg.is_active else 0
            h3 = cfg.hours_3_apic if cfg.is_active else 0
            tot_h1 = n1 * h1
            tot_h2 = n2 * h2
            tot_h3 = n3 * h3
            tot_h = tot_h1 + tot_h2 + tot_h3
            req_rooms = math.ceil(tot_h / 48.0) if tot_h > 0 else 0
            req_teachers = math.ceil(tot_h / 24.0) if tot_h > 0 else 0
            results.append(SubjectQuotaCalc(
                name=cfg.name, is_generalized=False,
                hours_1=h1, hours_2=h2, hours_3=h3,
                total_hours=tot_h, required_rooms=req_rooms, required_teachers=req_teachers,
                hours_level_1=tot_h1, hours_level_2=tot_h2, hours_level_3=tot_h3
            ))

        return results

    def _distribute_subject_classes(self, items: List[Tuple[str, int, int]], num_teachers: int) -> List[List[Tuple[str, int, int]]]:
        if num_teachers <= 0 or not items:
            return []
        if num_teachers == 1:
            return [list(items)]
            
        available_levels = sorted(list(set(it[2] for it in items)))
        if len(available_levels) <= 1:
            buckets = [[] for _ in range(num_teachers)]
            for it in sorted(items, key=lambda x: -x[1]):
                min_t = min(range(num_teachers), key=lambda t: sum(x[1] for x in buckets[t]))
                buckets[min_t].append(it)
            return buckets

        # Try exact optimization solver first
        res = self._solve_exact(items, num_teachers, available_levels)
        if res:
            return res
            
        # If not found or large instance, use deterministic pedagogical solver
        return self._solve_deterministic(items, num_teachers, available_levels)

    def _solve_exact(self, items: List[Tuple[str, int, int]], num_teachers: int, available_levels: List[int]) -> List[List[Tuple[str, int, int]]]:
        min_required_levels = min(2, len(available_levels))
        sorted_items = sorted(items, key=lambda x: (0 if x[2] == 3 else 1, -x[1], x[0]))
        
        best_alloc = None
        best_score = float("inf")
        
        current_alloc = [[] for _ in range(num_teachers)]
        current_hours = [0] * num_teachers
        current_3ac = [0] * num_teachers
        current_levels = [set() for _ in range(num_teachers)]
        
        states = 0
        max_states = 40000
        
        def backtrack(idx):
            nonlocal best_alloc, best_score, states
            states += 1
            if states > max_states:
                return
                
            if idx == len(sorted_items):
                for t in range(num_teachers):
                    if len(current_levels[t]) < min_required_levels:
                        return
                    if current_hours[t] > 24:
                        return
                
                t_3ac_cnt = sum(1 for t in range(num_teachers) if current_3ac[t] > 0)
                inversion_penalty = 0
                for t1 in range(num_teachers):
                    for t2 in range(num_teachers):
                        if t1 != t2:
                            if current_3ac[t1] > current_3ac[t2] and current_hours[t1] > current_hours[t2]:
                                inversion_penalty += (current_hours[t1] - current_hours[t2]) * 50
                                
                lev_penalty = sum(15 for t in range(num_teachers) if len(current_levels[t]) > 2)
                cnt_5h_pen = sum((sum(1 for it in current_alloc[t] if it[1] == 5) - 4) * 200 
                                 for t in range(num_teachers) if sum(1 for it in current_alloc[t] if it[1] == 5) > 4)
                h_range = max(current_hours) - min(current_hours)
                
                score = (t_3ac_cnt * 1000) + inversion_penalty + lev_penalty + cnt_5h_pen + h_range
                if score < best_score:
                    best_score = score
                    best_alloc = [list(b) for b in current_alloc]
                return
                
            item = sorted_items[idx]
            c_name, c_h, c_lvl = item
            
            seen_empty = False
            order = list(range(num_teachers))
            if c_lvl == 3:
                order.sort(key=lambda t: (-current_3ac[t], current_hours[t]))
            else:
                order.sort(key=lambda t: (0 if len(current_levels[t]) < min_required_levels else 1, current_hours[t]))
                
            for t in order:
                if current_hours[t] == 0:
                    if seen_empty:
                        continue
                    seen_empty = True
                    
                if current_hours[t] + c_h > 24:
                    continue
                if c_h == 5 and sum(1 for it in current_alloc[t] if it[1] == 5) >= 4:
                    continue
                    
                current_alloc[t].append(item)
                current_hours[t] += c_h
                if c_lvl == 3: current_3ac[t] += 1
                added_lvl = c_lvl not in current_levels[t]
                if added_lvl: current_levels[t].add(c_lvl)
                
                backtrack(idx + 1)
                
                current_alloc[t].pop()
                current_hours[t] -= c_h
                if c_lvl == 3: current_3ac[t] -= 1
                if added_lvl: current_levels[t].remove(c_lvl)

        backtrack(0)
        if best_alloc:
            best_alloc.sort(key=lambda b: (-sum(1 for x in b if x[2] == 3), sum(x[1] for x in b)))
        return best_alloc

    def _solve_deterministic(self, items: List[Tuple[str, int, int]], num_teachers: int, available_levels: List[int]) -> List[List[Tuple[str, int, int]]]:
        c3 = [it for it in items if it[2] == 3]
        c2 = [it for it in items if it[2] == 2]
        c1 = [it for it in items if it[2] == 1]
        
        buckets: List[List[Tuple[str, int, int]]] = [[] for _ in range(num_teachers)]
        
        h3 = c3[0][1] if c3 else 0
        if h3 == 5:
            max_3ac_per_t = 2
            target_3ac_hours = 18
        elif h3 == 4:
            max_3ac_per_t = 4
            target_3ac_hours = 20
        elif h3 == 3:
            max_3ac_per_t = 4
            target_3ac_hours = 15
        else:
            max_3ac_per_t = 4
            target_3ac_hours = 20

        n3 = len(c3)
        if n3 > 0:
            needed_3ac_t = (n3 + max_3ac_per_t - 1) // max_3ac_per_t
            needed_3ac_t = min(needed_3ac_t, num_teachers)
            for it in c3:
                best_t = min(range(needed_3ac_t), key=lambda t: sum(1 for x in buckets[t] if x[2] == 3))
                buckets[best_t].append(it)

        rem_c2 = list(c2)
        rem_c1 = list(c1)
        
        for t in range(num_teachers):
            if any(x[2] == 3 for x in buckets[t]):
                curr_h = sum(x[1] for x in buckets[t])
                if rem_c2 and curr_h + rem_c2[0][1] <= 24:
                    buckets[t].append(rem_c2.pop(0))
                    curr_h = sum(x[1] for x in buckets[t])
                elif rem_c1 and curr_h + rem_c1[0][1] <= 24:
                    buckets[t].append(rem_c1.pop(0))
                    curr_h = sum(x[1] for x in buckets[t])
                    
                while curr_h < target_3ac_hours:
                    added = False
                    if rem_c2 and curr_h + rem_c2[0][1] <= target_3ac_hours:
                        buckets[t].append(rem_c2.pop(0))
                        curr_h += buckets[t][-1][1]
                        added = True
                    elif rem_c1 and curr_h + rem_c1[0][1] <= target_3ac_hours:
                        buckets[t].append(rem_c1.pop(0))
                        curr_h += buckets[t][-1][1]
                        added = True
                    if not added:
                        break

        non_3ac_teachers = [t for t in range(num_teachers) if not any(x[2] == 3 for x in buckets[t])]
        
        for t in non_3ac_teachers:
            if rem_c1 and sum(x[1] for x in buckets[t]) + rem_c1[0][1] <= 24:
                buckets[t].append(rem_c1.pop(0))
            if rem_c2 and sum(x[1] for x in buckets[t]) + rem_c2[0][1] <= 24:
                buckets[t].append(rem_c2.pop(0))

        remaining_lower = rem_c1 + rem_c2
        remaining_lower.sort(key=lambda x: -x[1])
        
        for it in remaining_lower:
            candidates = []
            for t in non_3ac_teachers:
                ch = sum(x[1] for x in buckets[t])
                c5 = sum(1 for x in buckets[t] if x[1] == 5)
                if ch + it[1] <= 24 and not (it[1] == 5 and c5 >= 4):
                    candidates.append((ch, t))
            if candidates:
                candidates.sort()
                buckets[candidates[0][1]].append(it)
            else:
                candidates_all = []
                for t in range(num_teachers):
                    ch = sum(x[1] for x in buckets[t])
                    c5 = sum(1 for x in buckets[t] if x[1] == 5)
                    if ch + it[1] <= 24 and not (it[1] == 5 and c5 >= 4):
                        candidates_all.append((ch, t))
                if candidates_all:
                    candidates_all.sort()
                    buckets[candidates_all[0][1]].append(it)
                else:
                    min_t = min(range(num_teachers), key=lambda t: sum(x[1] for x in buckets[t]))
                    buckets[min_t].append(it)

        for t in range(num_teachers):
            lvls = set(x[2] for x in buckets[t])
            if len(lvls) < 2 and len(buckets[t]) > 0:
                t_lvl = list(lvls)[0]
                swapped = False
                for t2 in range(num_teachers):
                    if t2 == t:
                        continue
                    t2_lvls = set(x[2] for x in buckets[t2])
                    if len(t2_lvls) >= 2:
                        for i_t, item_t in enumerate(buckets[t]):
                            for i_t2, item_t2 in enumerate(buckets[t2]):
                                if item_t[1] == item_t2[1] and item_t2[2] != t_lvl:
                                    test_t2_lvls = set(x[2] for j, x in enumerate(buckets[t2]) if j != i_t2) | {item_t[2]}
                                    if len(test_t2_lvls) >= 2:
                                        buckets[t][i_t] = item_t2
                                        buckets[t2][i_t2] = item_t
                                        swapped = True
                                        break
                            if swapped:
                                break
                    if swapped:
                        break

        buckets.sort(key=lambda b: (-sum(1 for x in b if x[2] == 3), sum(x[1] for x in b)))
        return buckets

    def calculate_assignments(self) -> List[TeacherAssignment]:
        n1 = self.structure.classes_1_apic
        n2 = self.structure.classes_2_apic
        n3 = self.structure.classes_3_apic

        c1_list = [f"1APIC{i}" for i in range(1, n1 + 1)]
        c2_list = [f"2APIC{i}" for i in range(1, n2 + 1)]
        c3_list = [f"3APIC{i}" for i in range(1, n3 + 1)]

        assignments: List[TeacherAssignment] = []
        row_id = 1

        quotas = self.get_subject_quotas()

        shift_map = {
            "اللغة العربية": 0,
            "اللغة الفرنسية": 3,
            "الرياضيات": 6,
            "الاجتماعيات": 2,
            "التربية الإسلامية": 4,
            "علوم الحياة و الأرض": 1,
            "الكيمياء و الفيزياء": 5,
            "التربية البدنية": 7,
            "المعلوميات": 0,
            "اللغة الأجنبية الثانية (الإنجليزية)": 3,
            "التكنولوجيا الصناعية": 2,
            "التربية الأسرية": 4,
            "التربية التشكيلية / أو الموسيقية": 5,
        }

        for q in quotas:
            if q.total_hours <= 0:
                continue

            num_teachers = self.institution.teacher_counts_by_subject.get(q.name, q.required_teachers)
            if num_teachers <= 0:
                continue

            s = shift_map.get(q.name, 0)
            c1_s = (c1_list[s % len(c1_list):] + c1_list[:s % len(c1_list)]) if c1_list else []
            c2_s = (c2_list[s % len(c2_list):] + c2_list[:s % len(c2_list)]) if c2_list else []
            c3_s = (c3_list[s % len(c3_list):] + c3_list[:s % len(c3_list)]) if c3_list else []

            # Build class items
            items = []
            if q.hours_1 > 0:
                items.extend([(c, q.hours_1, 1) for c in c1_s])
            if q.hours_2 > 0:
                items.extend([(c, q.hours_2, 2) for c in c2_s])
            if q.hours_3 > 0:
                items.extend([(c, q.hours_3, 3) for c in c3_s])

            t_allocations = self._distribute_subject_classes(items, num_teachers)
            avail_levels_for_subj = set(it[2] for it in items)

            for t_i, t_items in enumerate(t_allocations):
                if not t_items:
                    continue
                def_name = f"أستاذ {q.name} {t_i + 1}"
                real_name = (self.institution.teacher_custom_names.get(def_name) or "").strip()
                teacher_name = real_name if real_name else def_name
                assigned_classes = [it[0] for it in t_items]
                tot_h = sum(it[1] for it in t_items)
                c1_cnt = len([it for it in t_items if it[2] == 1])
                c2_cnt = len([it for it in t_items if it[2] == 2])
                c3_cnt = len([it for it in t_items if it[2] == 3])
                levels = (1 if c1_cnt else 0) + (1 if c2_cnt else 0) + (1 if c3_cnt else 0)

                if tot_h == 24:
                    status = "نصاب كامل (24س)"
                elif c3_cnt > 0 and tot_h < 24:
                    status = f"نصاب مخفف للثالثة إعدادي ({tot_h}س)"
                elif tot_h < 24:
                    status = f"نصاب مخفف ({tot_h}س)"
                else:
                    status = f"نصاب {tot_h}س ✓"

                two_levels_ok = (levels >= 2) or (len(avail_levels_for_subj) <= 1)

                assignments.append(TeacherAssignment(
                    row_id=row_id,
                    subject=q.name,
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
