import process.process as process
import cv2

if __name__ == '__main__':
    image1 = cv2.imread("capture14.jpg")
    #黑白化
    image1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
    process.process(image1, debug_mode=-1)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
