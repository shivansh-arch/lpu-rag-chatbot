from rag_bot.pipeline import answer_question


def main():
    # Ask for student ID once
    student_id = input("Enter your student ID: ").strip()

    if not student_id:
        print("Student ID cannot be empty.")
        return

    print("\nLPU RAG Chatbot")
    print("Type 'exit' or 'quit' to stop.\n")

    while True:
        question = input("You: ").strip()

        # Skip empty questions
        if not question:
            print("Please enter a question.")
            continue

        # Exit condition
        if question.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        # Send question to the pipeline
        answer = answer_question(
            question,
            student_id
        )

        print(f"\nBot: {answer}\n")


if __name__ == "__main__":
    main()