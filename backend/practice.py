print("Temp conversion")

def celsius_to_fahrenheit(celsius):
    return(celsius * 9/5) + 32

def fahrenheit_to_celsius(fahrenheit):
    return(fahrenheit - 32) * 5/9

temp_c = int(input("Give a temprature in C: "))
temp_f = celsius_to_fahrenheit(temp_c)

print(f"{temp_c} C = {temp_f} F")

temp_f_ = int(input("Give a temprature in F: "))

temp_c_ = fahrenheit_to_celsius(temp_f_)

print(f"{temp_f_} F = {temp_c_} C")

def analyze_numbers(numbers):
    return {
        "Count ": len(numbers),
        "sum" : sum(numbers),
        "Average": sum(numbers) / len(numbers),
        "Max": max(numbers),
        "Min": min(numbers),
        "Range": max(numbers) - min(numbers)
    }
    
test_num = [1, 23, 44, 55, 6, 7, 8, 33, 9, 90, 3, 4, 5, 6, 7, 8, 9]
results = analyze_numbers(test_num)

print(f"Numbers: {test_num}")

for key, value in results.items():
    print(f"{key.capitalize()}: {value:.2f}")
    
    

def format_video_title(title):
    return ' '.join(word.capitalize() for word in title.split())


def generate_slug(title):
    return title.lower().replace(' ', '-').replace('-', '-')

video_title = "Learning pyton for streamscribe"
formated = format_video_title(video_title)
slug = generate_slug(formated)


print(f"Orignal: '{video_title}'")
print(f"Formated: '{formated}'")
print(f"Slug: '{slug}'")


videos = [
    {"id": 1, "title": "Python Tutorial", "duration":1200, "views": 1500},
    {"id": 2, "title": "Fast API Crash Course", "duration":3200, "views": 2500},
    {"id": 3, "title": "React Basics", "duration":1600, "views": 6500}
]


def get_total_duration(video_list):
    return sum(video['duration'] for video in video_list)

def get_most_video(video_list):
    return max(video_list, key= lambda v: v['views'])

total = get_total_duration(videos)
most_viewed = get_most_video(videos)

print(f"Total videos : {len(videos)}")
print(f"Total Duration: {total} seconds ({total/60:.1f} minutes)")
print(f"Most viewed: '{most_viewed['title']}' with {most_viewed['views']} views")

def validate_video_upload(file_size_mb, file_type):
    
    Max_size_mb = 100
    Allowed_types = ['mp4', 'avi', 'mov','mkv']
    
    errors = []
    
    if file_size_mb > Max_size_mb:
        errors.append(f"File to large: {file_size_mb}MB (max: {Max_size_mb} MB)")
        
    if file_type not in Allowed_types:
        errors.append(f"Invalid type: {file_type} (allowed: {', '.join(Allowed_types)})")
    
    if errors:
        return {"valid": False, "errors": errors}
    else:
        return {"valid": True, "message": "Upload approved!"}


test1 = validate_video_upload(50, 'mp4')
test2 = validate_video_upload(150, 'mp4')
test3 = validate_video_upload(50, 'wmv')

print("Test 1 (50MB, mp4):", test1)
print("Test 2 (150MB, mp4):", test2)
print("Test 3 (50MB, wmv):", test3)