import cv2
import json
import utm

def read_metadata_from_json(json_file):
    with open(json_file, 'r') as file:
        metadata = json.load(file)
    return metadata

def main(video_path, json_file):
    # Read metadata from JSON file
    metadata = read_metadata_from_json(json_file)

    # Open video file
    cap = cv2.VideoCapture(video_path)

    # if not cap.isOpened():
    #     print("Error: Couldn't open video file.")
    #     return

    # Get video properties
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Loop through frames
    for frame_number in range(frame_count):
        # Read frame
        frame_number += 1
        ret, frame = cap.read()
        if not ret:
            print("Error reading frame.")
            break

        # Get metadata for the current frame
        frame_metadata = metadata[frame_number]

        # Extract values from metadata
        chassis = frame_metadata.get('chassis')
        loco    = frame_metadata.get('localization')

        lat,lon = utm.to_latlon(loco['pose_x'], loco['pose_y'], 17, 'S')

        lat = round(lat,5)
        lon = round(lon,5)

        driving_mode = chassis['driving_mode']

        # Display values on the screen
        text = f'Frame: {frame_number}, Lat: {lat}, Lon: {lon}, Driving Mode: {driving_mode}'
        cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # Show the frame
        cv2.imshow('Video with Metadata', frame)

        # Break the loop if the user presses 'q'
        if cv2.waitKey(int(1000 / fps)) & 0xFF == ord('q'):
            break

    # Release video capture object and close window
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Specify the path to the video file and the JSON file
    video_path = "./videos/full_route/1698251665/1698251665_6mm.avi"
    met_file = "./videos/full_route/1698251665/1698251665_6mm.json"

      # Run the main function
    main(video_path, met_file)

