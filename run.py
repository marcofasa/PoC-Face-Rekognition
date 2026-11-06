import boto3
from PIL import Image
import io

session = boto3.Session(profile_name='default')
client = session.client('rekognition')


def create_session():
    response = client.create_face_liveness_session()

    session_id = response.get("SessionId")
    print('SessionId: ' + session_id)

    return session_id




def get_session_results(session_id, do_compare_faces=True):
    response = client.get_face_liveness_session_results(SessionId=session_id)
    confidence = response.get("Confidence")
    status = response.get("Status")
    reference_image = response.get("ReferenceImage")
    if reference_image is not None and 'Bytes' in reference_image:
        reference_image = reference_image['Bytes']
        show_image_from_bytes(reference_image)
        if do_compare_faces:
            compare_faces(reference_image)
    print('Confidence: ' + "{:.2f}".format(confidence) + "%")
    print('Status: ' + status)

    if status == 'SUCCEEDED':
        print('Face Liveness Session succeeded.')

    return status


def compare_faces(imageTarget, sourceFile="photo.jpg", ):
    imageSource = open(sourceFile, 'rb')

    response = client.compare_faces(SimilarityThreshold=80,
                                    SourceImage={'Bytes': imageSource.read()},
                                    TargetImage={'Bytes': imageTarget})

    for faceMatch in response['FaceMatches']:
        position = faceMatch['Face']['BoundingBox']
        similarity = str(faceMatch['Similarity'])
        print('The face at ' +
              str(position['Left']) + ' ' +
              str(position['Top']) +
              ' matches with ' + similarity + '% confidence')

    imageSource.close()
    # imageTarget.close()
    return len(response['FaceMatches'])




def show_image_from_bytes(image_bytes):
    image = Image.open(io.BytesIO(image_bytes))
    image.show()


if __name__ == "__main__":
    just_create_session_id = False
    session_id = None

    if just_create_session_id:
        print('Created a Face Liveness Session with ID: ' + create_session())
    elif session_id is not None:
        print('Using existing session ID: ' + session_id)
        input("Press Enter to get session results...")
        get_session_results(session_id)
    else:
        session_id = create_session()
        input("Press Enter to get session results...")
        get_session_results(session_id)
