from rest_framework import serializers, generics
from rest_framework.permissions import AllowAny

from books.models import Book


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ["id", "author", "title"]
        read_only_fields = ["id"]


# /books/
class BookList(generics.ListCreateAPIView):
    serializer_class = BookSerializer
    permission_classes = [AllowAny]
    queryset = Book.objects.all()


# /books/<pk:int>
class BookDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    lookup_field = "id"
    lookup_url_kwarg = "pk"
    permission_classes = [AllowAny]
