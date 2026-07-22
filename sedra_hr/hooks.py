app_name = "sedra_hr"
app_title = "Sedra HR"
app_publisher = "Mahmoud Tawfeek"
app_description = "Sedra HR customizations"
app_email = "mahmoudtawfeek815@gmail.com"
app_license = "mit"

fixtures = [
    {
        "dt": "Custom Field",
        "filters": [
            [
                "name",
                "in",
                [
                    "HR Settings-require_employee_checkin_photo",
                    "Employee Checkin-custom_employee_photo"
                ]
            ]
        ]
    }
]

doc_events = {
    "Employee Checkin": {
        "before_insert": "sedra_hr.sedra_hr.checkin_validation.validate_checkin"
    }
}

doctype_list_js = {
    "Employee Checkin": "public/js/employee_checkin_list.js"
}

doctype_js = {
    "Employee Checkin": "public/js/employee_checkin.js"
}