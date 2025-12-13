from django.db import models

class ScanResult(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    start_freq = models.FloatField()
    stop_freq = models.FloatField()
    image_path = models.CharField(max_length=255)
    raw_data = models.JSONField(default=list)

    def __str__(self):
        return f"Scan {self.id} - {self.created_at}"
