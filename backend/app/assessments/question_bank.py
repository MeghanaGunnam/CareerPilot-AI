TECHNICAL_ASSESSMENTS = [
    {
        "skill": "Java",
        "title": "Java Fundamentals Assessment",
        "description": (
            "Evaluates foundational Java knowledge including types, "
            "inheritance, collections, exceptions, and object-oriented concepts."
        ),
        "difficulty": "FOUNDATIONAL",
        "version": 1,
        "questions": [
            {
                "position": 1,
                "question_text": (
                    "Which keyword is used to inherit a class in Java?"
                ),
                "options": [
                    {"key": "A", "text": "implements"},
                    {"key": "B", "text": "extends"},
                    {"key": "C", "text": "inherits"},
                    {"key": "D", "text": "super"},
                ],
                "correct_option": "B",
                "explanation": (
                    "A Java class inherits another class using "
                    "the extends keyword."
                ),
            },
            {
                "position": 2,
                "question_text": (
                    "Which Java collection does not allow "
                    "duplicate elements?"
                ),
                "options": [
                    {"key": "A", "text": "List"},
                    {"key": "B", "text": "ArrayList"},
                    {"key": "C", "text": "Set"},
                    {"key": "D", "text": "LinkedList"},
                ],
                "correct_option": "C",
                "explanation": (
                    "The Set interface represents a collection "
                    "that does not contain duplicate elements."
                ),
            },
            {
                "position": 3,
                "question_text": (
                    "Which of the following is a checked "
                    "exception in Java?"
                ),
                "options": [
                    {
                        "key": "A",
                        "text": "NullPointerException",
                    },
                    {
                        "key": "B",
                        "text": "ArithmeticException",
                    },
                    {"key": "C", "text": "IOException"},
                    {
                        "key": "D",
                        "text": "ArrayIndexOutOfBoundsException",
                    },
                ],
                "correct_option": "C",
                "explanation": (
                    "IOException is a checked exception and "
                    "must generally be handled or declared."
                ),
            },
            {
                "position": 4,
                "question_text": (
                    "What is method overriding in Java?"
                ),
                "options": [
                    {
                        "key": "A",
                        "text": (
                            "Defining multiple methods with the "
                            "same name but different parameters"
                        ),
                    },
                    {
                        "key": "B",
                        "text": (
                            "A subclass providing its own "
                            "implementation of an inherited method"
                        ),
                    },
                    {
                        "key": "C",
                        "text": (
                            "Calling a private method from "
                            "another class"
                        ),
                    },
                    {
                        "key": "D",
                        "text": (
                            "Creating multiple objects from "
                            "the same class"
                        ),
                    },
                ],
                "correct_option": "B",
                "explanation": (
                    "Overriding occurs when a subclass provides "
                    "its own implementation of an inherited "
                    "method with a compatible signature."
                ),
            },
            {
                "position": 5,
                "question_text": (
                    "Which statement about Java String "
                    "objects is correct?"
                ),
                "options": [
                    {
                        "key": "A",
                        "text": "String objects are mutable",
                    },
                    {
                        "key": "B",
                        "text": "String objects are immutable",
                    },
                    {
                        "key": "C",
                        "text": "String cannot store empty text",
                    },
                    {
                        "key": "D",
                        "text": "String is a primitive type",
                    },
                ],
                "correct_option": "B",
                "explanation": (
                    "Java String objects are immutable after "
                    "creation."
                ),
            },
        ],
    },
    {
        "skill": "Critical Thinking",
        "title": "Critical Thinking Fundamentals Assessment",
        "description": (
            "Evaluates foundational reasoning through evidence "
            "evaluation, assumption checking, comparison of "
            "explanations, and conclusion selection."
        ),
        "difficulty": "FOUNDATIONAL",
        "version": 1,
        "questions": [
            {
                "position": 1,
                "question_text": (
                    "A team observes that application crashes "
                    "increased after a new release. What is the "
                    "best first conclusion?"
                ),
                "options": [
                    {
                        "key": "A",
                        "text": (
                            "The new release definitely caused "
                            "every crash."
                        ),
                    },
                    {
                        "key": "B",
                        "text": (
                            "The timing suggests a possible "
                            "relationship, but more evidence is "
                            "needed to establish the cause."
                        ),
                    },
                    {
                        "key": "C",
                        "text": (
                            "The release cannot be related "
                            "because the old version also crashed."
                        ),
                    },
                    {
                        "key": "D",
                        "text": (
                            "The application should immediately "
                            "be rewritten."
                        ),
                    },
                ],
                "correct_option": "B",
                "explanation": (
                    "An observed association is evidence worth "
                    "investigating, but timing alone does not "
                    "establish causation."
                ),
            },
            {
                "position": 2,
                "question_text": (
                    "Two reports disagree about whether a new "
                    "process improved productivity. What is the "
                    "most useful next step?"
                ),
                "options": [
                    {
                        "key": "A",
                        "text": (
                            "Accept the report with the larger "
                            "improvement."
                        ),
                    },
                    {
                        "key": "B",
                        "text": (
                            "Choose the report written most "
                            "recently."
                        ),
                    },
                    {
                        "key": "C",
                        "text": (
                            "Compare their data sources, "
                            "measurement methods, and assumptions."
                        ),
                    },
                    {
                        "key": "D",
                        "text": "Ignore both reports.",
                    },
                ],
                "correct_option": "C",
                "explanation": (
                    "Conflicting conclusions should be examined "
                    "by comparing the evidence, methods, and "
                    "assumptions supporting them."
                ),
            },
            {
                "position": 3,
                "question_text": (
                    "A model performs well on its training data "
                    "but poorly on unseen data. Which evidence "
                    "is most relevant before claiming that the "
                    "model is reliable?"
                ),
                "options": [
                    {
                        "key": "A",
                        "text": "The number of lines of code",
                    },
                    {
                        "key": "B",
                        "text": (
                            "Performance on appropriate "
                            "validation or test data"
                        ),
                    },
                    {
                        "key": "C",
                        "text": "The model's file size",
                    },
                    {
                        "key": "D",
                        "text": (
                            "How quickly the training script "
                            "was written"
                        ),
                    },
                ],
                "correct_option": "B",
                "explanation": (
                    "Evidence from unseen data is needed to "
                    "evaluate whether performance generalizes "
                    "beyond the training examples."
                ),
            },
            {
                "position": 4,
                "question_text": (
                    "A manager says, 'Every successful employee "
                    "I know works late, so working late causes "
                    "success.' What is the main reasoning issue?"
                ),
                "options": [
                    {
                        "key": "A",
                        "text": (
                            "The conclusion assumes causation "
                            "from limited observational evidence."
                        ),
                    },
                    {
                        "key": "B",
                        "text": (
                            "The statement contains too many "
                            "numbers."
                        ),
                    },
                    {
                        "key": "C",
                        "text": (
                            "The statement proves that working "
                            "late is necessary."
                        ),
                    },
                    {
                        "key": "D",
                        "text": (
                            "There is no possible relationship "
                            "between work hours and outcomes."
                        ),
                    },
                ],
                "correct_option": "A",
                "explanation": (
                    "The observation may suggest a hypothesis, "
                    "but it does not establish that working late "
                    "caused the successful outcomes."
                ),
            },
            {
                "position": 5,
                "question_text": (
                    "A company must choose between two systems. "
                    "System A is cheaper but has more failures. "
                    "System B costs more but has fewer failures. "
                    "What is the strongest decision approach?"
                ),
                "options": [
                    {
                        "key": "A",
                        "text": (
                            "Always select the cheaper system."
                        ),
                    },
                    {
                        "key": "B",
                        "text": (
                            "Always select the system with fewer "
                            "failures regardless of cost."
                        ),
                    },
                    {
                        "key": "C",
                        "text": (
                            "Compare cost, failure impact, "
                            "reliability requirements, and other "
                            "relevant evidence before deciding."
                        ),
                    },
                    {
                        "key": "D",
                        "text": (
                            "Choose whichever system was "
                            "evaluated first."
                        ),
                    },
                ],
                "correct_option": "C",
                "explanation": (
                    "A reasoned decision considers the relevant "
                    "trade-offs and evidence rather than relying "
                    "on one factor alone."
                ),
            },
        ],
    },
]