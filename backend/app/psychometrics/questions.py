RIASEC_QUESTIONS = [
    # Realistic — R
    {
        "id": "R01",
        "dimension": "R",
        "text": "I enjoy building, assembling, or repairing physical things.",
    },
    {
        "id": "R02",
        "dimension": "R",
        "text": "I like working with tools, machines, or technical equipment.",
    },
    {
        "id": "R03",
        "dimension": "R",
        "text": "I enjoy practical tasks where I can create something tangible.",
    },
    {
        "id": "R04",
        "dimension": "R",
        "text": "I prefer learning by doing rather than only reading about a task.",
    },
    {
        "id": "R05",
        "dimension": "R",
        "text": "I enjoy solving problems that involve equipment or physical systems.",
    },

    # Investigative — I
    {
        "id": "I01",
        "dimension": "I",
        "text": "I enjoy investigating why something works the way it does.",
    },
    {
        "id": "I02",
        "dimension": "I",
        "text": "I like analyzing information to discover patterns or explanations.",
    },
    {
        "id": "I03",
        "dimension": "I",
        "text": "I enjoy solving difficult logical or scientific problems.",
    },
    {
        "id": "I04",
        "dimension": "I",
        "text": "I like experimenting with different approaches to test an idea.",
    },
    {
        "id": "I05",
        "dimension": "I",
        "text": "I enjoy learning deeply about technical or scientific subjects.",
    },

    # Artistic — A
    {
        "id": "A01",
        "dimension": "A",
        "text": "I enjoy creating original designs, ideas, stories, or visual work.",
    },
    {
        "id": "A02",
        "dimension": "A",
        "text": "I like tasks that allow me to express my own ideas creatively.",
    },
    {
        "id": "A03",
        "dimension": "A",
        "text": "I enjoy finding imaginative ways to present information.",
    },
    {
        "id": "A04",
        "dimension": "A",
        "text": "I prefer work that gives me freedom to explore different ideas.",
    },
    {
        "id": "A05",
        "dimension": "A",
        "text": "I enjoy producing creative content, designs, or experiences.",
    },

    # Social — S
    {
        "id": "S01",
        "dimension": "S",
        "text": "I enjoy helping other people understand difficult topics.",
    },
    {
        "id": "S02",
        "dimension": "S",
        "text": "I like supporting people when they are trying to solve a problem.",
    },
    {
        "id": "S03",
        "dimension": "S",
        "text": "I enjoy teaching, mentoring, or guiding others.",
    },
    {
        "id": "S04",
        "dimension": "S",
        "text": "I like work that involves understanding people's needs.",
    },
    {
        "id": "S05",
        "dimension": "S",
        "text": "I enjoy collaborating with people to help them improve.",
    },

    # Enterprising — E
    {
        "id": "E01",
        "dimension": "E",
        "text": "I enjoy convincing people to support an idea or plan.",
    },
    {
        "id": "E02",
        "dimension": "E",
        "text": "I like taking responsibility for leading a group or project.",
    },
    {
        "id": "E03",
        "dimension": "E",
        "text": "I enjoy making decisions when several options are available.",
    },
    {
        "id": "E04",
        "dimension": "E",
        "text": "I like organizing people and resources to achieve a goal.",
    },
    {
        "id": "E05",
        "dimension": "E",
        "text": "I enjoy presenting ideas and encouraging others to act on them.",
    },

    # Conventional — C
    {
        "id": "C01",
        "dimension": "C",
        "text": "I enjoy organizing information in a clear and structured way.",
    },
    {
        "id": "C02",
        "dimension": "C",
        "text": "I like working with detailed records, data, or documentation.",
    },
    {
        "id": "C03",
        "dimension": "C",
        "text": "I enjoy tasks that require accuracy and careful attention to detail.",
    },
    {
        "id": "C04",
        "dimension": "C",
        "text": "I prefer having clear procedures when completing important tasks.",
    },
    {
        "id": "C05",
        "dimension": "C",
        "text": "I enjoy keeping information, schedules, or processes well organized.",
    },
]


QUESTION_BY_ID = {
    question["id"]: question
    for question in RIASEC_QUESTIONS
}


DIMENSION_NAMES = {
    "R": "Realistic",
    "I": "Investigative",
    "A": "Artistic",
    "S": "Social",
    "E": "Enterprising",
    "C": "Conventional",
}


RESPONSE_OPTIONS = [
    {
        "value": 1,
        "label": "Strongly dislike",
    },
    {
        "value": 2,
        "label": "Dislike",
    },
    {
        "value": 3,
        "label": "Neutral",
    },
    {
        "value": 4,
        "label": "Like",
    },
    {
        "value": 5,
        "label": "Strongly like",
    },
]