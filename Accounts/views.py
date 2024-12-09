from django.shortcuts import render
from .serializers import UserRegisterSerializer,UserProfileSerializer
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from .serializers import UserProfileSerializer
from .models import CustomUser
from rest_framework import generics, permissions
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
# Create your views here.
@api_view(["POST"],)
def user_registeration_view(request):
    if request.method == 'POST':
        serializer = UserRegisterSerializer(data=request.data)
        data={}
        if serializer.is_valid():
            account = serializer.save()
            data['username'] = account.username
            data['email'] = account.email
            token = Token.objects.get(user=account).key
            data['token'] = token
            
            # return serializer.data
            return Response({"message": "User created successfully", "user_data": data},status=status.HTTP_201_CREATED)
        else:
            data = serializer.errors
        return Response(data)
        
     
@api_view(['POST'])
class custom_login(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        email  =  request.data.get('email')
        password =  request.data.get('password')
        user = authenticate(request,username=email, password=password)
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.pk,
                'email': user.email
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)
        
@api_view(['POST'])
def logout_view(request):
    if request.method == 'POST':
        try:
            request.user.auth_token.delete()
            return Response({"message": "User logged out successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_user_status(request):
    """
    Returns the login status and details of the authenticated user.
    """
    if request.user.is_authenticated:
        # If the user is logged in, return user details
        return Response({
            "status": "Logged In",
            "detail": {
                "username": request.user.username,
                "email": request.user.email,
                "date_joined": request.user.date_joined.strftime("%Y-%m-%d"),
            }
        }, status=status.HTTP_200_OK)
    else:
        # If the user is not logged in, return anonymous status
        return Response({
            "status": "Not Logged In",
            "detail": "Anonymous User",
        }, status=status.HTTP_401_UNAUTHORIZED)
        
class UserProfileView(generics.RetrieveUpdateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_object(self):
        return self.request.user
# views.py@api_view(['PUT'])
@csrf_exempt  # Disable CSRF protection for this view (if needed)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    user = request.user  # Get the logged-in user
    
    # Log the incoming request data for debugging
    print("Request Data:", request.data)

    # Create the serializer and validate the data
    serializer = UserProfileSerializer(user, data=request.data, partial=True)  # partial=True allows partial updates
    
    if serializer.is_valid():
        # Save the profile data, including any uploaded image
        updated_user = serializer.save()

        # After saving, we can access the file URL
        profile_picture_url = updated_user.profile_picture.url if updated_user.profile_picture else None
        
        # Log the updated data for debugging
        print("Updated Data:", {
            "username": updated_user.username,
            "email": updated_user.email,
            "profile_picture": profile_picture_url,
        })
        
        # Return the response with updated user details
        return Response({
            "message": "Profile updated successfully", 
            "updated_user": {
                "username": updated_user.username,
                "email": updated_user.email,
                "profile_picture": profile_picture_url
            }
        }, status=status.HTTP_200_OK)
    
    # Log errors if the serializer is not valid
    print("Serializer Errors:", serializer.errors)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)