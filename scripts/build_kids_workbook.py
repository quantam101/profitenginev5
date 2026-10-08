#!/usr/bin/env python3
"""Little Engineers — professional workbook PDF builder.

Produces a school/homeschool-grade printable workbook:
cover, TOC, CSTA-aligned unit structure, teacher guide, rubric,
six units (three levels + teen extension), answer key with
rationale, glossary, and completion certificate.
"""
from fpdf import FPDF
import pathlib

import sys
OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "kids-workbook.pdf")
OUT.parent.mkdir(parents=True, exist_ok=True)

NAVY = (23, 42, 68)
TEAL = (14, 116, 120)
GOLD = (240, 173, 40)
LIGHT = (240, 244, 248)
GREY = (90, 98, 110)

# Per-unit accent colors (Brain Quest-style section coding)
GREEN = (47, 137, 74)
PURPLE = (124, 58, 150)
ORANGE = (222, 111, 34)
SKY = (32, 120, 168)
ROSE = (188, 58, 92)
INDIGO = (72, 74, 158)
UNIT_COLORS = {1: GREEN, 2: PURPLE, 3: ORANGE, 4: SKY, 5: ROSE, 6: INDIGO}


def esc(t: str) -> str:
    return (t.replace("\u2014", "-").replace("\u2013", "-")
             .replace("\u2192", "->").replace("\u201c", '"')
             .replace("\u201d", '"').replace("\u2018", "'")
             .replace("\u2019", "'").replace("\u2022", "-")
             .encode("latin-1", "replace").decode("latin-1"))


class WB(FPDF):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.accent = None       # active unit color -> margin ribbon
        self.unit_label = ""     # vertical label in the ribbon

    def add_page(self, *a, **k):
        super().add_page(*a, **k)
        if self.accent:
            w_rib = 15
            self.set_fill_color(*self.accent)
            self.rect(0, 0, w_rib, self.h, style="F")
            # vertical unit label
            self.set_text_color(255, 255, 255)
            self.set_font("helvetica", "B", 8)
            with self.rotation(90, 9, 250):
                self.text(9, 250, esc(self.unit_label.upper()))
            # circled page number at ribbon bottom
            self.set_fill_color(255, 255, 255)
            self.ellipse(2.5, self.h - 22, 10, 10, style="F")
            self.set_text_color(*self.accent)
            self.set_font("helvetica", "B", 9)
            num = str(self.page_no())
            tw = self.get_string_width(num)
            self.text(2.5 + (10 - tw) / 2, self.h - 15.6, num)
            self.set_text_color(0, 0, 0)
            self.l_margin = 24
            self.set_x(self.l_margin)

    def footer(self):
        if self.page_no() <= 2:
            return
        self.set_y(-14)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(*GREY)
        self.cell(0, 8, f"Little Engineers - {self.page_no()}", align="C")
        self.set_text_color(0, 0, 0)

    def h1(self, text, color=NAVY):
        self.set_x(self.l_margin)
        self.set_font("helvetica", "B", 20)
        self.set_text_color(*color)
        self.multi_cell(0, 10, esc(text))
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def h2(self, text, color=TEAL):
        self.set_x(self.l_margin)
        self.set_font("helvetica", "B", 13)
        self.set_text_color(*color)
        self.multi_cell(0, 7, esc(text))
        self.set_text_color(0, 0, 0)

    def body(self, text, size=11, style=""):
        self.set_x(self.l_margin)
        self.set_font("helvetica", style, size)
        self.multi_cell(0, 6, esc(text))

    def bullet(self, items, size=11):
        for it in items:
            self.set_x(self.l_margin + 4)
            self.set_font("helvetica", "", size)
            self.multi_cell(0, 6, "-  " + esc(it))

    def numbered(self, items, size=11, gap=8):
        for i, it in enumerate(items, 1):
            self.set_x(self.l_margin + 4)
            self.set_font("helvetica", "", size)
            self.multi_cell(0, gap, f"{i}.  " + esc(it))

    def lines(self, n, label=True):
        for _ in range(n):
            self.ln(9)
            self.set_x(self.l_margin + 4)
            self.set_draw_color(150, 158, 170)
            self.line(self.l_margin + 4, self.get_y(), self.w - self.r_margin - 4, self.get_y())

    def notebook(self, text):
        self.box("ENGINEER'S NOTEBOOK", text, fill=(255, 243, 205), edge=GOLD)

    def box(self, title, text, fill=LIGHT, edge=TEAL):
        self.set_x(self.l_margin)
        self.set_fill_color(*fill)
        self.set_draw_color(*edge)
        x, y = self.l_margin, self.get_y()
        w = self.w - self.l_margin - self.r_margin
        self.set_font("helvetica", "B", 11)
        h = 8 + 6 * (len(esc(text)) // 95 + text.count("\n") + 1)
        self.rect(x, y, w, h, style="DF")
        self.set_xy(x + 4, y + 3)
        self.set_font("helvetica", "B", 11)
        self.cell(w - 8, 6, esc(title), new_x="LMARGIN", new_y="NEXT")
        self.set_x(x + 4)
        self.set_font("helvetica", "", 10)
        self.multi_cell(w - 8, 6, esc(text))
        self.set_y(y + h + 4)

    def divider(self, title, subtitle, color=NAVY):
        # Full-color section cover (Brain Quest style): big circled unit
        # number, title, subtitle — the whole page is the accent color.
        saved = self.accent
        self.accent = None
        self.l_margin = 18
        self.add_page()
        self.pages_log[title] = self.page_no()
        self.set_fill_color(*color)
        self.rect(0, 0, self.w, self.h, style="F")
        self.ln(70)
        self.set_fill_color(255, 255, 255)
        self.ellipse(self.w / 2 - 22, 78, 44, 44, style="F")
        self.set_text_color(*color)
        self.set_font("helvetica", "B", 30)
        num = "".join(ch for ch in title if ch.isdigit()) or title[:2]
        self.set_xy(self.w / 2 - 22, 91)
        self.cell(44, 16, esc(num), align="C")
        self.set_y(140)
        self.set_text_color(255, 255, 255)
        self.set_font("helvetica", "B", 27)
        self.cell(0, 16, esc(title.split(" - ")[-1] if title.startswith("Unit") else title), align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("helvetica", "", 14)
        self.cell(0, 10, esc(subtitle), align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("helvetica", "I", 10)
        self.cell(0, 8, "Little Engineers Workbook", align="C")
        self.set_text_color(0, 0, 0)
        self.accent = saved
        self.add_page()


def build(pdf):
    pdf.pages_log = {}
    pdf.set_auto_page_break(True, margin=22)
    pdf.set_margins(18, 18, 18)

    # ── Cover     ──────────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, pdf.w, pdf.h, style="F")
    pdf.set_fill_color(*GOLD)
    pdf.rect(0, 96, pdf.w, 4, style="F")
    pdf.rect(0, 196, pdf.w, 4, style="F")
    pdf.set_y(110)
    pdf.set_font("helvetica", "B", 34)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 16, "LITTLE ENGINEERS", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 16)
    pdf.set_text_color(*GOLD)
    pdf.cell(0, 12, "Technology & Logic Workbook", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 13)
    pdf.set_text_color(220, 228, 238)
    pdf.cell(0, 10, "Printable STEM activities, puzzles, and coding foundations", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, "Grades 3-8  |  Ages 7-14  |  Screen-free", align="C")
    pdf.set_y(230)
    pdf.set_font("helvetica", "", 11)
    pdf.cell(0, 8, "Student Name: ______________________________", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "School / Program: __________________________", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Started: ____________   Completed: ____________", align="C")
    pdf.set_y(272)
    pdf.set_font("helvetica", "", 9)
    pdf.cell(0, 6, "Already Here LLC  |  alreadyherellc.com", align="C")

    # ── About / How to use ─────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1("About This Workbook")
    pdf.body(
        "Little Engineers is a print-and-use workbook that builds the thinking "
        "skills behind computer science - no device, account, or app required. "
        "Students work through six units that move from recognizing patterns to "
        "writing and debugging simple programs, understanding how computers and "
        "networks work, staying safe online, and (for older students) reading "
        "and writing real pseudocode."
    )
    pdf.ln(2)
    pdf.h2("Who it is for")
    pdf.bullet([
        "Classroom teachers needing a ready-made, low-prep CS supplement",
        "Homeschool families wanting structured, screen-free STEM practice",
        "After-school, library, and enrichment programs",
        "Tutors and intervention groups working with mixed ages",
    ])
    pdf.h2("How it is organized")
    pdf.body(
        "Each unit opens with an overview page listing learning objectives, the "
        "CSTA standards it supports, key vocabulary, and materials. Activities "
        "come in three tiers - Core (everyone), Practice (apply it), and "
        "Challenge (stretch) - so a single workbook serves ages 7-14. Each unit "
        "ends with a short Exit Ticket students can use to self-check."
    )
    pdf.h2("What you need")
    pdf.bullet([
        "This workbook, printed single-sided",
        "Pencils and a ruler",
        "Optional: scissors and glue for cut-out activities, a deck of cards "
        "and masking tape for the unplugged extensions",
    ])
    pdf.box("Time commitment",
            "6 units x 3 activity sets + 1 review game per unit. At one unit per "
            "week (2-3 sessions of 30-45 minutes), the workbook runs 6 weeks - a "
            "natural fit for a grading period or enrichment block.")

    # ── TOC ────────────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1("Contents")
    toc = [
        ("Facilitator Guide & Standards Alignment", "3"),
        ("Unit 1 - Patterns & Sequences", "6"),
        ("Unit 2 - If-Then Logic & Algorithms", "11"),
        ("Unit 3 - Number & Problem-Solving Puzzles", "16"),
        ("Unit 4 - How Computers & Networks Work", "21"),
        ("Unit 5 - Data, Passwords & Staying Safe", "26"),
        ("Unit 6 - Teen Extension: Real Programs", "31"),
        ("Assessment Rubric", "36"),
        ("Answer Key & Explanations", "37"),
        ("Glossary", "42"),
        ("Certificate of Completion", "43"),
    ]
    for name, pg in toc:
        pdf.set_x(pdf.l_margin)
        pdf.set_font("helvetica", "", 12)
        pdf.cell(150, 9, esc(name))
        pdf.set_font("helvetica", "I", 11)
        pdf.cell(0, 9, pg, align="R")
        pdf.ln(1)

    # ── Facilitator guide ──────────────────────────────────────────────────
    pdf.divider("Facilitator Guide", "For teachers, parents, and program leads")
    pdf.h2("Learning objectives")
    pdf.body("By the end of this workbook, students will be able to:")
    pdf.bullet([
        "Identify, extend, and create patterns, and state the rule a pattern follows",
        "Write, follow, and debug step-by-step instructions (algorithms)",
        "Use if-then rules to describe decisions a program makes",
        "Decompose a problem into smaller, solvable parts",
        "Describe how a computer takes input, processes it, and produces output",
        "Trace how a message travels across a network",
        "Explain what makes a strong password and safe online behavior",
        "(Extension) Read and write simple pseudocode using variables and loops",
    ])
    pdf.h2("CSTA standards alignment (CSTA K-12 CS Standards, 2017)")
    pdf.set_font("helvetica", "", 10)
    rows = [
        ("Unit 1 Patterns", "1B-DA-07, 1B-AP-10", "Recognize and describe patterns; develop algorithms"),
        ("Unit 2 Algorithms", "1B-AP-08, 1B-AP-11, 2-AP-10", "Model processes, decompose problems, flowchart algorithms"),
        ("Unit 3 Number Puzzles", "1B-DA-06, 1B-AP-09", "Organize and analyze data; solve problems systematically"),
        ("Unit 4 Computers & Networks", "1B-CS-02, 1B-NI-04, 2-NI-04", "Hardware/software systems; model network communication"),
        ("Unit 5 Safety & Data", "1B-IC-18, 1B-NI-05, 2-IC-23", "Keep information safe; describe computing impacts"),
        ("Unit 6 Teen Programs", "2-AP-11, 2-AP-12, 2-AP-19", "Variables, control structures, document programs"),
    ]
    pdf.set_fill_color(*LIGHT)
    for i, (a, b, c) in enumerate(rows):
        y = pdf.get_y()
        if i == 0:
            pdf.set_font("helvetica", "B", 10)
        else:
            pdf.set_font("helvetica", "", 10)
        pdf.set_x(pdf.l_margin)
        pdf.cell(52, 8, esc(a), border=1, fill=(i == 0))
        pdf.cell(48, 8, esc(b), border=1, fill=(i == 0))
        pdf.multi_cell(0, 8, esc(c), border=1, fill=(i == 0))
    pdf.ln(4)
    pdf.h2("Pacing")
    pdf.body(
        "Suggested schedule: one unit per week. Session 1 = mini-lesson + Core "
        "activity. Session 2 = Practice activity. Session 3 = Challenge + Exit "
        "Ticket + the unplugged game. Every unit also works standalone - use "
        "single units as sub plans, early-finisher packs, or remediation."
    )
    pdf.h2("Differentiation")
    pdf.bullet([
        "Ages 7-9 / Grades 3-4: do Core + Practice with adult or buddy support; "
        "accept verbal rule statements instead of written ones.",
        "Ages 10-12 / Grades 5-6: complete all three tiers independently.",
        "Ages 12-14 / Grades 7-8: add Unit 6 and require Challenge tiers; "
        "have students create their own puzzles for peers.",
    ])
    pdf.h2("Assessment")
    pdf.body(
        "Use the 4-point rubric (page 36) with the Exit Tickets. Mastery target: "
        "3+ on the rubric for each unit. The answer key gives intended answers "
        "AND acceptable alternatives - in logic work, a different-but-defensible "
        "answer with a stated rule demonstrates mastery."
    )
    pdf.box("Unplugged extensions",
            "Each unit ends with a no-materials or low-materials game you can run "
            "in a classroom, living room, or library program room - pattern "
            "claps, human robot mazes (masking-tape grid), message relay, and "
            "password elections.")

    # ── UNITS ─────────────────────────────────────────────────────────────
    def unit(num, title, ages, stds, objectives, vocab, materials, lesson, sections):
        pdf.accent = UNIT_COLORS.get(num, NAVY)
        pdf.unit_label = f"UNIT {num} - {title}"
        pdf.divider(f"Unit {num}", title + "  |  Ages " + ages, color=pdf.accent)
        pdf.h2("Unit overview")
        pdf.body(f"CSTA alignment: {stds}")
        pdf.h2("You will learn to")
        pdf.bullet(objectives)
        pdf.h2("Key vocabulary")
        pdf.body(vocab)
        pdf.body(f"Materials: {materials}")
        pdf.ln(2)
        pdf.h2("Mini-lesson")
        pdf.body(lesson)
        for sec_title, sec_body, items in sections:
            pdf.add_page()
            pdf.h2(sec_title, color=NAVY)
            pdf.body(sec_body)
            pdf.ln(2)
            if items:
                pdf.numbered(items)
                pdf.lines(1)
        pdf.add_page()
        pdf.h2("Exit Ticket", color=NAVY)
        pdf.body("Before you move on, show what you know:")


    # UNIT 1
    unit(1, "Patterns & Sequences", "7-9",
         "1B-DA-07, 1B-AP-10",
         ["Find the rule a pattern follows", "Extend a pattern forward and backward",
          "Build your own pattern and write its rule", "Explain why computers love patterns"],
         "pattern - something that repeats by a rule;  sequence - items in order;  "
         "rule - the instruction that makes the pattern;  algorithm - a set of steps that always works.",
         "pencil only.",
         "A pattern is anything that repeats by a rule. Computers are pattern "
         "machines: they spot patterns in photos, music, and numbers faster than "
         "any person. The skill is not guessing the next item - it is saying the "
         "RULE out loud. 'Add 2' is a rule. 'Bigger' is not.\n\n"
         "Work every problem the same way: (1) look at the first three items, "
         "(2) say what changed, (3) say the rule, (4) use the rule to continue.",
         [
            ("Core - Find the rule",
             "Continue each pattern for two more items, then write the rule.",
             ["Circle, square, circle, square, circle, ___, ___",
              "2, 4, 6, 8, ___, ___   Rule: ______________",
              "A, B, C, A, B, C, ___, ___   Rule: ______________",
              "5, 10, 15, 20, ___, ___   Rule: ______________",
              "Z, Y, X, Z, Y, X, ___, ___   Rule: ______________",
              "1, 1, 2, 1, 1, 2, ___, ___   Rule: ______________",
              "100, 90, 80, ___, ___   Rule: ______________",
              "Draw your own 6-item pattern. Write its rule: ______________"]),
            ("Practice - Pattern detective",
             "One item in each row breaks the rule. Find it and fix it.",
             ["3, 6, 9, 11, 15   Broken item: ____  Fix: ____",
              "Mon, Tue, Wed, Fri, Thu   Broken item: ____  Fix: ____",
              "2, 4, 8, 16, 30   Broken item: ____  Fix: ____",
              "A1, B2, C3, D5   Broken item: ____  Fix: ____",
              "A pattern has 4, 8, 12, 16...  Is 26 in it? Why or why not?"]),
            ("Challenge - Grow it",
             "Patterns can grow in two directions and two rules at once.",
             ["Continue backward AND forward:  ___, 7, 14, 21, ___",
              "Two rules at once: 1, 2, 4, 8, 16, ___ (each step doubles)",
              "Make a shape pattern with a rule that uses BOTH color and size.",
              "Write a number pattern where the rule is 'add the last two numbers'. "
              "Start with 1, 1. What are the next four? (This is a famous sequence.)",
              "Explain to a partner why a computer can check 1,000 pattern rows "
              "in the time you check one."]),
         ])
    pdf.bullet([
        "State the rule for: 10, 20, 30, 40...  ______________",
        "What makes a good rule?  ______________",
        "One thing you can now do that a computer does too: ______________",
    ])
    pdf.notebook("Did you know? Your brain finds patterns the same way search engines do - by checking what repeats. Saying the RULE is the real skill.")
    pdf.box("Unplugged game - Pattern Claps",
            "Leader claps a pattern (clap, clap, stomp). Group continues it. "
            "Then a student leads. Rule: the group must say the rule before "
            "continuing. Switch leaders until everyone has made a pattern.")

    # UNIT 2
    unit(2, "If-Then Logic & Algorithms", "8-11",
         "1B-AP-08, 1B-AP-11, 2-AP-10",
         ["Write step-by-step instructions someone can follow exactly",
          "Use IF / THEN / ELSE to describe decisions",
          "Find and fix the bug in a set of steps",
          "Explain why order matters in an algorithm"],
         "algorithm - steps that always finish a task;  condition - a question that "
         "is true or false;  bug - a mistake in the steps;  debug - to find and fix a bug.",
         "pencil; for the maze, draw a grid or use masking tape on the floor.",
         "An algorithm is a recipe for a computer: exact steps, in exact order. "
         "If any step is missing or out of order, the 'program' fails. Computers "
         "decide using conditions: IF something is true, THEN do this, ELSE do "
         "that. Real programs are mostly thousands of these tiny decisions.\n\n"
         "Debugging - finding the one wrong step - is the skill employers pay "
         "for. A good debugger tests one change at a time.",
         [
            ("Core - If-then rules",
             "Finish each rule so a robot could follow it.",
             ["IF it is raining, THEN ______________________",
              "IF the homework folder is empty, THEN ______________________",
              "IF the battery is below 10%, THEN ______________________",
              "IF (raining) THEN take umbrella, ELSE ______________________",
              "Write your own safety rule for crossing a street: "
              "IF ______________ THEN ______________"]),
            ("Practice - Be the robot",
             "Robot commands: FORWARD, LEFT, RIGHT. On the grid, the robot "
             "starts at bottom-left (S) and must reach the star (*) at "
             "top-right.\n\nDraw your own 5x5 grid, mark S and *, then write "
             "the program (list of commands) that solves it.",
             ["Write your program as a numbered list of commands.",
              "How many commands did it take? ____",
              "Can you solve it with FEWER commands? Write the shorter program.",
              "Deliberately change one command. What happens? (This is a bug.)"]),
            ("Challenge - Debug like a pro",
             "Each program has exactly one bug. Find it and write the fix.",
             ["Program 'make a sandwich': 1) put jelly on bread 2) get bread out "
              "3) put on peanut butter 4) close sandwich. Bug: ____  Fix: ____",
              "Program 'get ready for school': brush teeth, put on shoes, eat "
              "breakfast, leave. Bug: ____  Fix: ____",
              "Robot grid program: FORWARD, FORWARD, LEFT, FORWARD - the robot "
              "hit a wall at step 3. The fix changes only ONE command. What is it?",
              "A teammate's program works but takes 20 commands; yours takes 8. "
              "Whose is 'better'? Explain what makes an efficient algorithm."]),
         ])
    pdf.bullet([
        "An algorithm is ______________________",
        "IF / THEN / ELSE is used when a program needs to ______________",
        "The bug I found today was ______________ and I fixed it by ______________",
    ])
    pdf.notebook("Every recipe, sport play, and board-game turn is an algorithm. Debugging yours is exactly what real programmers do all day.")
    pdf.box("Unplugged game - Human Robot",
            "Tape a 4x4 grid on the floor. One student is the robot (eyes closed "
            "or looking away), one is the programmer who reads commands, one is "
            "the debugger watching for errors. Rotate roles. Add 'obstacle' "
            "squares to raise difficulty.")

    # UNIT 3
    unit(3, "Numbers & Problem-Solving Puzzles", "8-12",
         "1B-DA-06, 1B-AP-09",
         ["Solve balance and missing-number puzzles systematically",
          "Break a big problem into smaller parts",
          "Check an answer by working backward",
          "Solve logic grid puzzles by eliminating impossible options"],
         "decompose - break a problem into smaller pieces;  data - information a "
         "computer stores;  eliminate - rule out impossible answers.",
         "pencil.",
         "Programmers decompose problems: instead of 'solve the puzzle,' think "
         "'solve this row first.' Balance puzzles, missing-number grids, and "
         "logic grids all reward the same habit - work one constraint at a time, "
         "eliminate what is impossible, then check by working backward.",
         [
            ("Core - Balance the scale",
             "Both sides must be equal. Fill in the missing number.",
             ["5 + 3 = ___ + 2", "4 + ___ = 7 + 7", "10 + ___ = 6 + 9",
              "___ + 8 = 12 + 4", "9 + 9 = ___ + 13",
              "3 + ___ + 2 = 5 + 6"]),
            ("Practice - Word problems programmers actually write",
             "Solve. Show the steps, not just the answer.",
             ["A video is 90 seconds and you watch 12 seconds each day. How many "
              "days to finish it?",
              "Your allowance is $8/week. A game costs $40. How many weeks to "
              "save for it? What if you save half of each week plus $2?",
              "A school has 4 classrooms with 6 computers each. How many total? "
              "If 5 are broken, how many work?",
              "Screen time rule: 30 minutes per day on weekdays, 60 on weekend "
              "days. How many minutes per week? How many hours?"]),
            ("Challenge - Logic grid",
             "Three friends - Ada, Bo, and Cy - each have a different pet "
             "(cat, dog, fish) and a different favorite subject (math, art, "
             "science). Clues: (1) Ada does not have the fish. (2) Bo's favorite "
             "subject is science. (3) The dog owner loves math. (4) Cy has the "
             "fish.\n\nDraw a 3x3 grid (names vs pets, names vs subjects) and "
             "mark X for impossible and O for certain.",
             ["Who has the cat? ____", "Who loves art? ____",
              "Write one sentence explaining how clue 4 unlocked the puzzle."]),
         ])
    pdf.bullet([
        "Decompose means ______________________",
        "The strategy that helped me most today was ______________",
        "A problem I can decompose outside this workbook: ______________",
    ])
    pdf.box("Unplugged game - Estimation jar",
            "Fill a jar with objects (beans, buttons). Teams estimate, then "
            "decompose: count a small handful, estimate how many handfuls fill "
            "the jar, multiply. Closest estimate explains their method.")

    # UNIT 4
    unit(4, "How Computers & Networks Work", "9-12",
         "1B-CS-02, 1B-NI-04, 2-NI-04",
         ["Name the input, processing, and output of everyday devices",
          "Trace a message across the internet step by step",
          "Explain what hardware and software each do",
          "Describe what happens when you press send"],
         "input - what goes in;  processing - the thinking work;  output - what "
         "comes out;  network - connected devices;  server - a computer that answers "
         "requests for many users;  router - traffic director for a home network.",
         "pencil.",
         "Every computing device does three things: takes INPUT, does PROCESSING, "
         "makes OUTPUT. A toaster: bread + lever in, heating, toast out. A phone "
         "playing a video: your tap in, decoding, picture and sound out.\n\n"
         "Networks pass messages like relay races: your phone hands the message "
         "to a router, the router to your internet provider, to big backbone "
         "servers, and back down to the other person's phone - in milliseconds.",
         [
            ("Core - Input, processing, output",
             "For each device, list its input, the processing it does, and the output.",
             ["Toaster", "Digital watch", "Smartphone camera app",
              "Elevator button panel", "School attendance scanner"]),
            ("Practice - Trace the message",
             "You text 'hi' to a friend. Order the steps, then add the missing one.",
             ["Put in order: the cell tower, your phone, your friend's phone, "
              "network servers.", "What device sits between your phone and the "
              "internet at home? ____",
              "A video call freezes. Using the chain phone -> router -> "
              "provider -> servers -> phone, name TWO places the problem "
              "could be.",
              "Which step travels fastest - inside your house or between "
              "cities? Why?"]),
            ("Challenge - Design the system",
             "Apply input -> processing -> output as a designer.",
             ["Design an automatic dog feeder: list inputs (buttons, timers, "
              "sensors), processing rules, outputs (motor, alert).",
              "Your school wants to know which lunch is most popular. Describe "
              "the input you'd collect, how a computer would process it, and "
              "what output report it should produce.",
              "A smart doorbell sends you a video when someone arrives. Trace "
              "the message path like the texting example."]),
         ])
    pdf.bullet([
        "Input / processing / output for a fridge: ______________",
        "A server is ______________________",
        "Today I traced a message through ______________",
    ])
    pdf.box("Unplugged game - Message relay",
            "Teams line up. A message travels down the line by whisper (like "
            "packets through routers). Compare first and last versions. Then "
            "repeat with 'error checking': each person must repeat the message "
            "back before passing it on - accuracy improves, speed drops. That "
            "trade-off is real networking.")

    # UNIT 5
    unit(5, "Data, Passwords & Staying Safe", "9-12",
         "1B-IC-18, 1B-NI-05, 2-IC-23",
         ["Explain what personal data is and why it has value",
          "Judge password strength and build strong ones",
          "Spot common online tricks (phishing, fake urgency)",
          "Decide what is safe to share and what is private"],
         "data - information about you;  phishing - fake messages that try to "
         "steal information;  password - a secret handshake only you know;  "
         "private - for you and trusted adults only.",
         "pencil.",
         "Computers store data - facts about people. Names, birthdays, photos, "
         "locations, and passwords are data worth protecting. A strong password "
         "is long and mixes letters, numbers, and symbols; 'password123' can be "
         "guessed in seconds, while a long random phrase takes years.\n\n"
         "Safety rules that real engineers use: never share passwords (even with "
         "friends), check who sent a message before clicking, and when something "
         "online feels rushed or scary - stop and ask an adult.",
         [
            ("Core - Strong or weak?",
             "Rate each password STRONG or WEAK and say why in one line.",
             ["password123", "fluffy", "K9!mangoTree-77", "letmein",
              "PurpleTigerDances2!", "your pet's name",
              "Now write your own strong password pattern (don't use a real one)."]),
            ("Practice - Sort the data",
             "Label each item SAFE to share publicly or PRIVATE.",
             ["Your favorite pizza topping", "Your home address",
              "Your birth date", "A drawing you made", "Your school's name",
              "Your password hints", "Your phone number",
              "Write the rule you used to decide: ______________"]),
            ("Challenge - Spot the trick",
             "Each message has a red flag. Name it.",
             ["'URGENT!!! Your account closes in 1 hour - click now!'  Red flag: ____",
              "'Hi, this is your teacher, send me your login.'  Red flag: ____",
              "'You won a prize! Enter your address to claim.'  Red flag: ____",
              "A friend asks for your game password 'just for a minute.' "
              "What do you say? Write the reply.",
              "Why do scammers always add urgency? Explain the trick."]),
         ])
    pdf.bullet([
        "A strong password is ______________ and ______________",
        "The red flag I will watch for is ______________",
        "Data I keep private: ______________",
    ])
    pdf.box("Unplugged game - Password election",
            "Groups invent three passwords and present them. Class votes on the "
            "strongest and explains why. Rule: candidates may NOT be real "
            "passwords anyone uses.")

    # UNIT 6 — teen extension
    unit(6, "Teen Extension: Real Programs", "12-14",
         "2-AP-11, 2-AP-12, 2-AP-19",
         ["Read and write pseudocode with variables",
          "Use loops to repeat work without rewriting steps",
          "Trace a program line by line and predict the output",
          "Document what a program does so others can use it"],
         "variable - a named box that stores a value;  loop - repeat steps;  "
         "pseudocode - program logic written in plain language;  trace - follow "
         "each line and record what changes.",
         "pencil.",
         "Real programs store values in variables, make decisions with IF/ELSE, "
         "and repeat with loops (FOR, WHILE). Pseudocode writes the same logic "
         "in plain language:\n\n"
         "    score = 0\n"
         "    FOR each question:\n"
         "        IF correct THEN score = score + 1\n"
         "    DISPLAY score\n\n"
         "Tracing - following each line and writing down what every variable "
         "holds - is how professionals find bugs without running anything.",
         [
            ("Core - Trace it",
             "Trace each program. Write the final value of each variable.",
             ["x = 3;  x = x + 4;  x = x * 2   -> x = ___",
              "total = 0;  FOR i = 1 to 4: total = total + i   -> total = ___",
              "count = 0;  FOR letter in 'ROBOT': count = count + 1  -> count = ___",
              "a = 5; b = 2; IF a > b THEN a = a - b ELSE b = b + a   -> a=___, b=___"]),
            ("Practice - Write the pseudocode",
             "Write pseudocode for each task - a program a teammate could read "
             "and implement without asking questions.",
             ["Count how many items in a shopping list cost more than $5.",
              "Ask for a player's name and score; say 'You win!' if score > 100, "
              "else 'Try again'.",
              "A locker combination: loop asking for a code until it equals "
              "246 or the user has tried 3 times.",
              "Document your program #3 in two sentences a non-programmer "
              "could understand."]),
            ("Challenge - Find the bug",
             "This program should print the numbers 1 to 5. It prints 1, 1, 1... "
             "forever.\n\n    i = 1\n    WHILE i <= 5:\n        DISPLAY i\n",
             ["What is the bug? ____",
              "Write the corrected program.",
              "Add a line so it prints only EVEN numbers up to 10.",
              "An infinite loop is a bug. Name one place a loop SHOULD be "
              "infinite on purpose (hint: a device that must never stop)."]),
         ])
    pdf.bullet([
        "A variable is ______________",
        "The difference between FOR and WHILE: ______________",
        "Today I traced ______________ and learned ______________",
    ])
    pdf.box("Unplugged game - Living program",
            "Students act out a program. One holds a variable card ('score = 0'), "
            "others read lines aloud, the variable-holder updates their card. "
            "The class watches state change in real time - the exact skill of "
            "tracing, embodied.")

    # ── Rubric ────────────────────────────────────────────────────────────
    pdf.accent = None
    pdf.unit_label = ""
    pdf.divider("Assessment Rubric", "Score each unit's Exit Ticket 1-4")
    pdf.set_font("helvetica", "", 10)
    rubric = [
        ("Score", "Understanding", "Application", "Explanation"),
        ("4 - Exceeds", "States the rule/concept precisely",
         "Solves Challenge tier, creates own example",
         "Explains reasoning clearly, teaches a peer"),
        ("3 - Meets", "Correct rule/concept with minor slips",
         "Solves Core + Practice independently",
         "Explains most reasoning in own words"),
        ("2 - Approaching", "Partial concept; needs prompts",
         "Completes Core with some help",
         "Partial explanation; some gaps"),
        ("1 - Beginning", "Does not yet grasp the concept",
         "Needs step-by-step support on Core",
         "Cannot yet explain choices"),
    ]
    for i, row in enumerate(rubric):
        pdf.set_x(pdf.l_margin)
        if i == 0:
            pdf.set_font("helvetica", "B", 10)
            pdf.set_fill_color(*LIGHT)
        else:
            pdf.set_font("helvetica", "", 10)
        widths = [32, 50, 52, 52]
        y = pdf.get_y()
        for c, w in zip(row, widths):
            pdf.set_xy(pdf.l_margin + sum(widths[:row.index(c)]), y)
            pdf.multi_cell(w, 6, esc(c), border=1, fill=(i == 0))
        pdf.set_y(y + 6 * 2 + 2)
    pdf.ln(4)
    pdf.body(
        "Record per unit: Unit 1 __  Unit 2 __  Unit 3 __  Unit 4 __  "
        "Unit 5 __  Unit 6 __   |   Mastery target: 3+ per unit."
    )

    # ── Answer key ─────────────────────────────────────────────────────────
    pdf.divider("Answer Key", "Intended answers + acceptable alternatives")
    keys = [
        ("Unit 1", [
            "Core: 1) square, circle 2) 10, 12 (add 2) 3) A, B (ABC repeats) "
            "4) 25, 30 (add 5) 5) Z, Y (ZYX repeats) 6) 1, 1 (112 repeats) "
            "7) 70, 60 (subtract 10) 8) any stated rule is correct",
            "Practice: 1) 11 -> 12 2) Fri/Thu swapped 3) 30 -> 32 "
            "4) D5 -> D4 5) No - rule is add 4; 26-4=22 not in the sequence "
            "(or: 26 is not a multiple of 4 pattern from 4)",
            "Challenge: 1) 0 and 28 2) 32 3) check stated rule uses color+size "
            "4) 1,1,2,3,5,8 - next four: 2, 3, 5, 8 (Fibonacci) "
            "5) computers repeat the same check millions of times per second",
        ]),
        ("Unit 2", [
            "Core: any sensible action is correct; ELSE requires an alternative "
            "action (e.g., 'leave the umbrella home')",
            "Practice: shortest program exists; on an open 5x5 grid it is 8 "
            "commands (4 forward + turns). Extra steps that still reach the "
            "star are correct but less efficient",
            "Challenge: 1) steps 1 and 2 are out of order (jelly before bread) "
            "2) breakfast before brushing teeth 3) change LEFT to RIGHT "
            "(or swap positions) 4) fewer steps = efficient IF it still works; "
            "a 'better' program is correct AND short",
        ]),
        ("Unit 3", [
            "Core: 1) 6 2) 10 3) 5 4) 8 5) 5 6) 6",
            "Practice: 1) 8 days (7 days = 84s, needs day 8) 2) 5 weeks; "
            "half+$2 = $6/week -> 7 weeks 3) 24 total, 19 work "
            "4) 270 min = 4.5 hours",
            "Challenge: Cy has fish; Bo loves science; dog owner loves math, so "
            "dog owner is Ada or Cy - Cy has fish, so Ada has the dog and loves "
            "math; Bo has the cat... wait: Ada has dog (math), Cy has fish, Bo "
            "has cat and loves science, Cy loves art. Cat: Bo. Art: Cy.",
        ]),
        ("Unit 4", [
            "Core (sample): toaster - input: bread+lever/setting, processing: "
            "heating, output: toast; watch - input: button press, processing: "
            "time calculation, output: display; accept any correct IPO triple",
            "Practice: order = your phone -> cell tower/router -> network "
            "servers -> friend's phone; the home router sits between phone and "
            "internet; freeze could be router or provider link",
            "Challenge: dog feeder - inputs: schedule button, bowl sensor; "
            "processing: IF time AND bowl empty THEN release food; outputs: "
            "motor, done-alert. Any complete IPO design is acceptable",
        ]),
        ("Unit 5", [
            "Core: weak: password123, fluffy, letmein, pet name (short/guessable/"
            "dictionary); strong: K9!mangoTree-77, PurpleTigerDances2! "
            "(long, mixed)",
            "Practice: SAFE - pizza topping, drawing; PRIVATE - address, birth "
            "date, school name (debatable - accept reasoned), password hints, "
            "phone number. Rule: anything that identifies or locates you stays "
            "private",
            "Challenge: 1) fake urgency 2) impersonation 3) prize bait asking "
            "for personal data 4) any polite refusal is correct 5) urgency "
            "stops you from thinking - that IS the trick",
        ]),
        ("Unit 6", [
            "Core: 1) x = 14 2) total = 10 3) count = 5 4) a = 3, b = 2",
            "Practice (sample): FOR item in list: IF price > 5 THEN "
            "count = count + 1. Locker: tries = 0; WHILE code != 246 AND "
            "tries < 3: ask, tries = tries + 1",
            "Challenge: 1) i is never incremented - i stays 1 forever; fix: add "
            "i = i + 1 inside the loop 2) add 'i = i + 1' 3) start i = 2 and "
            "i = i + 2 (or IF i is even) 4) e.g., a pacemaker, a thermostat's "
            "monitor loop - devices that must run forever",
        ]),
    ]
    for name, items in keys:
        pdf.h2(name, color=NAVY)
        pdf.bullet(items, size=10)
        pdf.ln(2)

    # ── Glossary ───────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.pages_log["Glossary"] = pdf.page_no()
    pdf.h1("Glossary")
    gloss = [
        ("Algorithm", "A set of exact steps that always finishes a task."),
        ("Bug", "A mistake in a program or plan. Debugging = finding and fixing it."),
        ("Condition", "A question a program asks that is true or false (IF/THEN/ELSE)."),
        ("Data", "Information a computer stores - numbers, text, facts about people."),
        ("Decompose", "Break a big problem into smaller pieces you can solve."),
        ("Input / Processing / Output", "The three things every device does: what goes in, the work, what comes out."),
        ("Loop", "Program instructions that repeat (FOR, WHILE)."),
        ("Network", "Devices connected so they can pass messages."),
        ("Pattern", "Anything that repeats by a rule."),
        ("Phishing", "A fake message that tricks people into giving away private information."),
        ("Pseudocode", "Program logic written in plain language, readable by people."),
        ("Router", "The traffic director between a home network and the internet."),
        ("Server", "A computer that answers requests for many users at once."),
        ("Variable", "A named box a program stores a value in."),
    ]
    for term, definition in gloss:
        pdf.set_x(pdf.l_margin)
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(52, 7, esc(term))
        pdf.set_font("helvetica", "", 11)
        pdf.multi_cell(0, 7, esc(definition))

    # ── Certificate ────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.pages_log["Certificate"] = pdf.page_no()
    pdf.set_fill_color(*NAVY)
    pdf.rect(10, 10, pdf.w - 20, pdf.h - 20, style="D")
    pdf.set_draw_color(*GOLD)
    pdf.set_line_width(1.2)
    pdf.rect(14, 14, pdf.w - 28, pdf.h - 28, style="D")
    pdf.set_y(70)
    pdf.set_font("helvetica", "B", 26)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 14, "Certificate of Completion", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 13)
    pdf.set_text_color(*GREY)
    pdf.cell(0, 10, "This certifies that", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_font("helvetica", "B", 20)
    pdf.cell(0, 12, "__________________________________", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 12)
    pdf.set_text_color(*GREY)
    pdf.cell(0, 10, "has completed all six units of the", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "B", 15)
    pdf.set_text_color(*TEAL)
    pdf.cell(0, 10, "Little Engineers: Technology & Logic Workbook", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(16)
    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(*GREY)
    pdf.cell(95, 8, "Date: ______________", align="C")
    pdf.cell(0, 8, "Facilitator: ______________", align="C")
    pdf.set_y(252)
    pdf.set_font("helvetica", "", 9)
    pdf.cell(0, 6, "Already Here LLC  |  alreadyherellc.com", align="C")


def main():
    # Two-pass build: pass 1 collects real section start pages so the
    # Contents page lists accurate page numbers instead of guesses.
    probe = WB()
    probe.section_pages = {}
    build(probe)
    pdf = WB()
    pdf.section_pages = probe.pages_log
    build(pdf)
    pdf.output(str(OUT))
    print("wrote", OUT, pdf.page_no(), "pages")


main()
