from django.db import models


class Student(models.Model):

    usn = models.CharField(
        max_length=20,
        unique=True
    )

    name = models.CharField(
        max_length=100
    )

    email = models.EmailField(
        max_length=100,
        blank=True,
        null=True
    )

    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    college = models.CharField(
        max_length=150,
        default='JVIT'
    )

    degree = models.CharField(
        max_length=50,
        default='BE'
    )

    branch = models.CharField(
        max_length=80,
        default='CSE'
    )

    scheme = models.CharField(
        max_length=20,
        default='2022'
    )

    semester = models.IntegerField(
        default=1
    )

    def __str__(self):

        return self.usn


class Result(models.Model):

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE
    )

    semester = models.IntegerField(
        default=1
    )

    subject_code = models.CharField(
        max_length=30
    )

    subject_name = models.CharField(
        max_length=120
    )

    internal_marks = models.IntegerField(
        default=0
    )

    external_marks = models.IntegerField(
        default=0
    )

    total_marks = models.IntegerField(
        default=0
    )

    grade = models.CharField(
        max_length=5,
        default='F'
    )

    result = models.CharField(
        max_length=20,
        default='PASS'
    )

    def save(self, *args, **kwargs):

        self.total_marks = (
            self.internal_marks +
            self.external_marks
        )

        if self.total_marks >= 90:

            self.grade = 'O'

        elif self.total_marks >= 80:

            self.grade = 'A+'

        elif self.total_marks >= 70:

            self.grade = 'A'

        elif self.total_marks >= 60:

            self.grade = 'B+'

        elif self.total_marks >= 50:

            self.grade = 'B'

        elif self.total_marks >= 40:

            self.grade = 'P'

        else:

            self.grade = 'F'

        if (
            self.total_marks >= 40 and
            self.external_marks >= 18
        ):

            self.result = 'PASS'

        else:

            self.result = 'BACKLOG'

            self.grade = 'F'

        super().save(*args, **kwargs)

    def __str__(self):

        return self.subject_name


class Notice(models.Model):

    title = models.CharField(
        max_length=200
    )

    message = models.TextField()

    date = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.title
    
class Complaint(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )

    subject = models.CharField(max_length=150)
    message = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return self.subject
    
