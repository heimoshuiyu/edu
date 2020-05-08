from django.views import View
from django.utils.timezone import localtime
from django.forms import Form, IntegerField, MultipleChoiceField, DateTimeField, CharField
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from account.models import User
from course.models import Course, CourseInstance
from .models import Booking
import json


class BookingListAPI(View):
    def get(self, request):
        class BookingListAPIGetForm(Form):
            offset = IntegerField(initial=1, required=False)
            limit = IntegerField(initial=10, required=False)
            choices = (
                ("course", "course"),
                ("start_date", "start_date"),
                ("end_date", "end_date"),
                ("teacher", "teacher"),
                ("student", "student"),
                ("info", "info"),
            )
            column = MultipleChoiceField(choices=choices)

        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = BookingListAPIGetForm(data)
        if form.is_valid():
            cleaned_data = form.clean()

            if cleaned_data['offset'] is None:
                cleaned_data['offset'] = 0
            if cleaned_data['limit'] is None:
                cleaned_data['limit'] = 10

            result = list(User.objects.all()[
                          cleaned_data['offset']:cleaned_data['offset']+cleaned_data['limit']].values('id', *cleaned_data['column']))

            if 'date' in cleaned_data['column']:
                for each in result:
                    each['date'] = localtime(each['date'])

            return JsonResponse({
                'status': 200,
                'message': 'Success',
                'data': result,
            })
        else:
            return JsonResponse({
                'status': 400,
                'message': form.errors
            }, status=400)

    def post(self, request):
        class BookingListAPIPostForm(Form):
            course = IntegerField()
            start_date = DateTimeField()
            end_date = DateTimeField()
            teacher = IntegerField()
            info = CharField(required=False)

        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = BookingListAPIPostForm(data)
        if form.is_valid():
            cleaned_data = form.clean()

            try:
                cleaned_data['teacher'] = User.objects.get(
                    pk=cleaned_data['teacher'])
            except Exception as e:
                return JsonResponse({
                    'status': 400,
                    'message': 'TeacherNotFound',
                }, status=400)

            try:
                cleaned_data['course'] = Course.objects.get(
                    pk=cleaned_data['course'])
            except Exception as e:
                return JsonResponse({
                    'status': 400,
                    'message': 'CourseNotFound',
                }, status=400)

            if (cleaned_data['start_date'] > cleaned_data['end_date']) or (cleaned_data['start_date'] < cleaned_data['course'].start_date) or (cleaned_data['end_date'] > cleaned_data['course'].end_date):
                return JsonResponse({
                    'status': 400,
                    'message': 'InvalidDate',
                }, status=400)

            crash_booking = Booking.objects.filter(Q(start_date__gte=cleaned_data['start_date'], start_date__lt=cleaned_data['end_date'], teacher=cleaned_data['teacher']) | Q(
                end_date__gte=cleaned_data['end_date'], end_date__lt=cleaned_data['end_date'], teacher=cleaned_data['teacher']))

            if crash_booking:
                return JsonResponse({
                    'status': 400,
                    'message': 'TimeCrash',
                }, status=400)

            booking = Booking(course=cleaned_data['course'], start_date=cleaned_data['start_date'],
                              end_date=cleaned_data['end_date'], teacher=cleaned_data['teacher'], info=cleaned_data['info'])
            booking.save()
            return JsonResponse({
                'status': 200,
                'message': 'Success'
            })
        else:
            return JsonResponse({
                'status': 400,
                'message': form.errors
            }, status=400)


class BookingAPI(View):
    def get(self, request, booking_id):
        class BookingAPIGetForm(Form):
            choices = (
                ("course", "course"),
                ("start_date", "start_date"),
                ("end_date", "end_date"),
                ("teacher", "teacher"),
                ("student", "student"),
                ("info", "info"),
            )
            column = MultipleChoiceField(choices=choices)

        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = BookingAPIGetForm(data)
        if form.is_valid():
            cleaned_data = form.clean()

            try:
                result = list(Booking.objects.filter(pk=booking_id).values(
                    'id', *cleaned_data['column']))
            except Exception as e:
                return JsonResponse({
                    'status': 404,
                    'message': 'Not Found',
                }, status=404)

            if result == []:
                return JsonResponse({
                    'status': 404,
                    'message': 'Not Found',
                    'data': [],
                }, status=404)

            if 'start_date' in cleaned_data['column']:
                for each in result:
                    each['start_date'] = localtime(each['start_date'])
            if 'end_date' in cleaned_data['column']:
                for each in result:
                    each['end_date'] = localtime(each['end_date'])

            return JsonResponse({
                'status': 200,
                'message': 'Success',
                'data': result,
            })
        else:
            return JsonResponse({
                'status': 400,
                'message': form.errors
            }, status=400)

    def patch(self, request, booking_id):
        class BookingAPIPatchForm(Form):
            start_date = DateTimeField(required=False)
            end_date = DateTimeField(required=False)
            student = IntegerField(required=False)
            info = CharField(required=False)

        try:
            data = json.loads(request.body)

        except:
            return JsonResponse({
                'status': 400,
                'message': 'JSONDecodeError'
            }, status=400)

        form = BookingAPIPatchForm(data)
        if form.is_valid():
            try:
                booking = Booking.objects.get(
                    pk=booking_id)
            except Exception as e:
                return JsonResponse({
                    'status': 404,
                    'message': 'Not Found',
                }, status=404)

            cleaned_data = form.clean()

            if (cleaned_data['start_date'] > cleaned_data['end_date']) or (cleaned_data['start_date'] < cleaned_data['course'].start_date) or (cleaned_data['end_date'] > cleaned_data['course'].end_date):
                return JsonResponse({
                    'status': 400,
                    'message': 'InvalidDate',
                }, status=400)

            crash_booking = Booking.objects.filter(Q(start_date__gte=cleaned_data['start_date'], start_date__lt=cleaned_data['end_date'], student=booking.student) | Q(
                end_date__gte=cleaned_data['end_date'], end_date__lt=cleaned_data['end_date'], student=booking.student))

            if crash_booking:
                return JsonResponse({
                    'status': 400,
                    'message': 'TimeCrash',
                }, status=400)

            if cleaned_data['start_date'] is not None:
                booking.start_date = cleaned_data['start_date']

            if cleaned_data['end_date'] is not None:
                booking.start_date = cleaned_data['end_date']

            if cleaned_data['student'] is not None:
                try:
                    cleaned_data['student'] = User.objects.get(
                        pk=cleaned_data['student'])
                except Exception as e:
                    return JsonResponse({
                        'status': 400,
                        'message': 'StudentNotFound',
                    }, status=400)
                booking.student = cleaned_data['student']

            if 'info' in data:
                booking.info = cleaned_data['info']

            booking.save()
            return JsonResponse({
                'status': 200,
                'message': 'Success',
            })
        else:
            return JsonResponse({
                'status': 400,
                'message': form.errors
            }, status=400)

    def delete(self, request, booking_id):
        try:
            booking = Course.objects.get(pk=booking_id)
        except Exception as e:
            return JsonResponse({
                'status': 404,
                'message': 'Not Found',
            }, status=404)

        booking.delete()

        return JsonResponse({
            'status': 200,
            'message': 'Success',
        })
