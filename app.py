import cv2
import numpy as np
import time

def main():
    # Initialize webcam capture (default camera index 0)
    webcam = cv2.VideoCapture(0)
    if not webcam.isOpened():
        print("❌ Could not access the camera. Please check your webcam connection.")
        return

    # Allow the webcam time to warm up
    time.sleep(2)
    print("📸 Capturing initial background... please remain still")

    # Capture the initial background frame and prepare it for running average
    success, initial_frame = webcam.read()
    if not success:
        print("❌ Failed to capture initial background frame.")
        return
    initial_frame = cv2.flip(initial_frame, 1)  # Mirror the frame horizontally
    background_accumulator = initial_frame.astype(np.float32)  # Use float32 for accumulation

    # Hyperparameter: rate at which the background adapts to changes
    background_update_alpha = 0.04

    print("✅ Dynamic background initialized. Press ESC to exit.")

    while webcam.isOpened():
        success, frame = webcam.read()
        if not success:
            print("❌ Failed to read frame from webcam.")
            break

        frame = cv2.flip(frame, 1)  # Mirror horizontally for natural interaction

        # Convert current frame from BGR to HSV color space for color detection
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Define HSV ranges to detect the red color (red wraps around HSV space)
        lower_red_range1 = np.array([0, 100, 50])
        upper_red_range1 = np.array([10, 255, 255])
        lower_red_range2 = np.array([170, 100, 50])
        upper_red_range2 = np.array([180, 255, 255])

        # Generate masks for the two red ranges and combine them
        mask_red_1 = cv2.inRange(hsv_frame, lower_red_range1, upper_red_range1)
        mask_red_2 = cv2.inRange(hsv_frame, lower_red_range2, upper_red_range2)
        combined_red_mask = cv2.add(mask_red_1, mask_red_2)

        # Clean up the mask using morphological operations to reduce noise
        kernel = np.ones((3, 3), np.uint8)
        mask_opened = cv2.morphologyEx(combined_red_mask, cv2.MORPH_OPEN, kernel, iterations=2)
        mask_dilated = cv2.dilate(mask_opened, kernel, iterations=1)

        # Invert mask to get the region without the cloak
        mask_without_cloak = cv2.bitwise_not(mask_dilated)

        # Update the background dynamically only in areas without the cloak
        cv2.accumulateWeighted(frame.astype(np.float32), background_accumulator,
                               background_update_alpha, mask=mask_without_cloak)
        # Convert the accumulated background to 8-bit for display
        dynamic_background = cv2.convertScaleAbs(background_accumulator)

        # Extract cloak area from background and rest of the scene from current frame
        cloak_area = cv2.bitwise_and(dynamic_background, dynamic_background, mask=mask_dilated)
        visible_area = cv2.bitwise_and(frame, frame, mask=mask_without_cloak)

        # Combine both parts to get the final output frame
        output_frame = cv2.addWeighted(cloak_area, 1, visible_area, 1, 0)

        # Display the final composited frame and the mask (for debugging purposes)
        cv2.imshow("🪄 Invisibility Cloak with Dynamic Background", output_frame)
        cv2.imshow("🎭 Red Color Mask (Debug View)", mask_dilated)

        # Exit loop if ESC key is pressed
        if cv2.waitKey(1) & 0xFF == 27:
            break

    # Release resources and close windows
    webcam.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
