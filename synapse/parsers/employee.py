# Copyright 2007 Memorial Sloan-Kettering Cancer Center
# 
#     This file is part of Synapse.
# 
#     Synapse is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     Synapse is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with Synapse.  If not, see <http://www.gnu.org/licenses/>.




from library.synapse.models import Employee, Department, EmployeeDepartment
from library.synapse.util import split_name, kill_gremlins

import csv
import datetime
import codecs


class EmployeeParser(object):
    def __init__(self, content, year):
        self.content = kill_gremlins(content)
        if year in ('BLANK', u'BLANK') or not year:
            self.year = datetime.datetime.now().year
        else:
            self.year = year
        self._store_upload()
        self.empids_in_csv = []
        self.empids_cc = []
        for row in self.get_reader():
            self.empids_in_csv.append(row['EMPLID'])
            self.empids_cc.append({'emp_id': row['EMPLID'], 'cost_center': row['DEPTID']})
        return None
        
    def _store_upload(self):
        # set the output file name to a standard name with a timestamp
        self.out_name = "/tmp/uploads/emp_file_%s.csv" % datetime.datetime.isoformat(datetime.datetime.now())
        emp_file_out = codecs.open(self.out_name, "wb", 'ascii', 'replace')
        emp_file_out.write(kill_gremlins(self.content))
        emp_file_out.close()
        return None
        
    def get_reader(self):
        # assume user has whacked off the first few lines (5 normally) 
        # turn it into a CSV instance
        reader = csv.DictReader(open(self.out_name, "Ur"))
        return reader
        
    def create_new_departments(self):
        """creates any departments that are not already in the database"""
        for row in self.get_reader():
            Department.objects.get_or_create(cost_center=row['DEPTID'], defaults={'name': row['DEPARTMENT NAME'],
                                             'short_name': row['DEPARTMENT NAME']})
        return None
        
    def create_new_employees(self):
        """creates any employees that are not already in the database"""
        for row in self.get_reader():
            fname, mname, lname = split_name(row['NAME'])
            employee, employee_created = Employee.objects.get_or_create(emp_id=row['EMPLID'], 
                                           defaults={'first_name': fname,
                                           'middle_name':mname, 'last_name': lname,
                                           'job_title': row['JOB_TITLE']})
            print "Employee:", employee
            print "Employee Created: ", employee_created
            department = Department.objects.get(cost_center=row['DEPTID'])
            EmployeeDepartment.objects.get_or_create(employee=employee, department=department)
        return None
        
    def deactivate_employee(self, employee):
        """Marks an employee's database record as no longer employed, sets end date to current year
            for associated employee_department"""
        # get related records in EmployeeDepartment
        employee_departments = EmployeeDepartment.objects.filter(employee=employee)
        # mark employee as not currently employed
        employee.currently_employed = False
        employee.save()
        # for each related record in EmployeeDepartment
        for employee_department in employee_departments:
            # if year_end is null
            if not employee_department.year_end:                    
                # set year_end 
                employee_department.year_end = self.year
                employee_department.save()
        return None

    def update_employee_departments(self, employee):
        """Updates employee_department associations based on data in CSV, adds
           new association as needed"""
        csv_cost_center = None
        for row in self.get_reader():
            if row['EMPLID'] == employee.emp_id:
                csv_cost_center = row['DEPTID']
        if csv_cost_center:
            department = Department.objects.get(cost_center=csv_cost_center)
            employee_departments = EmployeeDepartment.objects.filter(employee=employee)
            current_employee_department, created = EmployeeDepartment.objects.get_or_create(employee=employee,
                                                   department=department, defaults={'year_begin':self.year})
            if created:
                print "new EmployeeDepartment created: %s" % current_employee_department.department.name
                for employee_department in employee_departments:
                    if employee_department is not current_employee_department and not employee_department.year_end:
                        employee_department.year_end = self.year
                        employee_department.save()
        return None
        
    def parse(self):
        e_count_start = Employee.objects.count()
        d_count_start = Department.objects.count()
        ed_count_start = EmployeeDepartment.objects.count()
        
        self.create_new_departments()
                    
        # for each employee in database
        employees = Employee.objects.all()
        for employee in employees:
            # if employee not in the uploaded csv
            if employee.emp_id not in self.empids_in_csv:
                # mark the employee as no longer employed
                self.deactivate_employee(employee)
            # else if employee in empids_in_csv
            else:
                # update the employee's associated department records
                self.update_employee_departments(employee)
            
        # create any employees not already in database
        self.create_new_employees()
                 
        e_count_end = Employee.objects.count()
        d_count_end = Department.objects.count()
        ed_count_end = EmployeeDepartment.objects.count()
        new_employees = e_count_end - e_count_start
        new_departments = d_count_end - d_count_start
        new_eds = ed_count_end - ed_count_start
        status = {'new_employees': new_employees, 'new_departments':new_departments,
                  'new_eds': new_eds}
        return status                        