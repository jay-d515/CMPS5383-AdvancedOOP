employees = [{
    "name": "Jadyn",
    "salary": 100000
}]

def add_employee(name, salary):
    emp = {
        "name": name,
        "salary": salary
    }
    employees.append(emp)
    
def remove_employee(name):
    for i, emp in enumerate(employees):
        employees.pop(i)
        print(employees)
        

for i in range(3):
    name = input("Enter employee name: ")
    remove_employee(name)
    
while True:
    option = input("press 1 for adding, press 2 for removing, q for quit.")
    
    if option == '1':
        name = input("Enter employee name: ")
        salary = int(input("Enter employee salary: "))
        add_employee(name, salary)
        
    if option == '2':
        name = input("Enter employee name: ")
        remove_employee(name)
        
    if option == 'q':
        break