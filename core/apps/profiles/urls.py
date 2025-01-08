from django.urls import path

from apps.profiles.views import ProfileView, ShippingAddressView, ShippingAddressViewID

urlpatterns = [
    path("", ProfileView.as_view()),
    path("shipping_addresses/", ShippingAddressView.as_view()),
    path("shipping_addresses/detail/<uuid:id>/", ShippingAddressViewID.as_view()),
]
