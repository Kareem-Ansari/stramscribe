print("Welcome to streamscribe devlopment")


name = input("What is your name: ")

print(f"\n Hello, {name}")
print(f"Today {name} is writing some new code and setting up the project ")

num = [1, 2, 3, 4, 5, 6, 7, 8, 9]

print(f"numbers: {num}")
print(f"Sum: {sum(num)}")
print(f"Average: {sum(num) / len(num):.2f}")
print(f"Max: {max(num)}")
print(f"Min: {min(num)}")

video_metadata = {
    "title" :"My first video", 
    "duration": "125",
    "Uploaded_py": name, 
    "Status": "Processing"
}

print("\n Video Metadata Preview")

for key, value in video_metadata.items():
    print(f"{key}: {value}")
    
    