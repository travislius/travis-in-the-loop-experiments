#!/usr/bin/env python3
"""Aggregate runs/*/result.json -> results.json + RESULTS.md"""
import json, glob, statistics as st
from pathlib import Path
H = Path(__file__).resolve().parent
R = [json.load(open(f)) for f in sorted(glob.glob(str(H / "runs/*/result.json")))]
S = []
for c, name in [("A", "No skill"), ("B", "Skill: instructions only"), ("C", "Skill + script")]:
    rs = [r for r in R if r["cond"] == c]; n = len(rs)
    k = lambda key: sum(bool(r["check"].get(key)) for r in rs)
    S.append({"cond": c, "name": name, "n": n, "pass": k("pass"), "numbers_correct": k("numbers_correct"), "house_format_exact": k("house_format_exact"),
              "total_correct": k("total_correct"), "categories_all_correct": sum(r["check"]["categories_correct"] == r["check"]["categories_total"] for r in rs),
              "flags_correct": k("flags_correct"), "skill_loaded": sum(bool(r["skill_loads"]) for r in rs), "script_used": sum(r["script_runs"] > 0 for r in rs),
              "median_wall_s": st.median(r["wall_seconds"] for r in rs), "median_output_tokens": st.median(r["usage"]["output"] for r in rs),
              "median_prompt_tokens": st.median(r["usage"]["input"] + r["usage"]["cache_hit"] for r in rs), "median_model_steps": st.median(r["steps"] for r in rs),
              "catalog_message_chars": st.median(r["catalog_message_chars"] for r in rs)})
skill_b = (H / "skills/B/expense-report/SKILL.md").read_text(); fm = skill_b.split("---")[1]
ctx = {"catalog_entry_chars_added_by_expense_skill": S[1]["catalog_message_chars"] - S[0]["catalog_message_chars"], "frontmatter_chars": len(fm), "skill_md_B_chars": len(skill_b),
       "skill_md_C_chars": len((H / "skills/C/expense-report/SKILL.md").read_text()), "script_chars": len((H / "skills/C/expense-report/scripts/build_report.py").read_text()), "note": "tokens ~ chars/4 (rough)"}
json.dump({"summary": S, "context_cost": ctx, "runs": len(R)}, open(H / "results.json", "w"), indent=1)
print(json.dumps(S, indent=1)); print(ctx)
