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
                "question_text": "Which keyword is used to inherit a class in Java?",
                "options": [
                    {"key": "A", "text": "implements"},
                    {"key": "B", "text": "extends"},
                    {"key": "C", "text": "inherits"},
                    {"key": "D", "text": "super"},
                ],
                "correct_option": "B",
                "explanation": "A Java class inherits another class using the extends keyword.",
            },
            {
                "position": 2,
                "question_text": "Which Java collection does not allow duplicate elements?",
                "options": [
                    {"key": "A", "text": "List"},
                    {"key": "B", "text": "ArrayList"},
                    {"key": "C", "text": "Set"},
                    {"key": "D", "text": "LinkedList"},
                ],
                "correct_option": "C",
                "explanation": "The Set interface represents a collection that does not contain duplicate elements.",
            },
            {
                "position": 3,
                "question_text": "Which of the following is a checked exception in Java?",
                "options": [
                    {"key": "A", "text": "NullPointerException"},
                    {"key": "B", "text": "ArithmeticException"},
                    {"key": "C", "text": "IOException"},
                    {"key": "D", "text": "ArrayIndexOutOfBoundsException"},
                ],
                "correct_option": "C",
                "explanation": "IOException is a checked exception and must generally be handled or declared.",
            },
            {
                "position": 4,
                "question_text": "What is method overriding in Java?",
                "options": [
                    {
                        "key": "A",
                        "text": "Defining multiple methods with the same name but different parameters",
                    },
                    {
                        "key": "B",
                        "text": "A subclass providing its own implementation of an inherited method",
                    },
                    {
                        "key": "C",
                        "text": "Calling a private method from another class",
                    },
                    {
                        "key": "D",
                        "text": "Creating multiple objects from the same class",
                    },
                ],
                "correct_option": "B",
                "explanation": (
                    "Overriding occurs when a subclass provides its own "
                    "implementation of an inherited method with a compatible signature."
                ),
            },
            {
                "position": 5,
                "question_text": "Which statement about Java String objects is correct?",
                "options": [
                    {"key": "A", "text": "String objects are mutable"},
                    {"key": "B", "text": "String objects are immutable"},
                    {"key": "C", "text": "String cannot store empty text"},
                    {"key": "D", "text": "String is a primitive type"},
                ],
                "correct_option": "B",
                "explanation": "Java String objects are immutable after creation.",
            },
        ],
    }
]