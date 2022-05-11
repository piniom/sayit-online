from django.db import models
from django.contrib.auth.models import User
from PIL import Image
import os


def crop_center(pil_img, crop_width, crop_height):
    img_width, img_height = pil_img.size
    return pil_img.crop(((img_width - crop_width) // 2,
                         (img_height - crop_height) // 2,
                         (img_width + crop_width) // 2,
                         (img_height + crop_height) // 2))


def crop_max_square(pil_img):
    return crop_center(pil_img, min(pil_img.size), min(pil_img.size))


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')

    def __str__(self):
        return f'{self.user.username} Profile'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        img = Image.open(self.image.path)

        head, tail = os.path.split(self.image.path)
        new_path = head + '/' + str(self.user.id) + '.png'

        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img = crop_max_square(img)
            img.thumbnail(output_size)
            # img.save(new_path)
            img.save(self.image.path)
