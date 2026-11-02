"""
community.py
Defines the Community hierarchy. Community is the parent class holding
members and posted resources. DepartmentCommunity and CourseCommunity
override membership rules differently.
"""


class Community:
    """Parent class. Holds members and resources, open membership by default."""

    def __init__(self, name):
        self.name = name
        self.members = []      # composition: a Community has Users
        self.resources = []    # composition: a Community has Resources

    def add_member(self, user):
        """Default rule: anyone may join."""
        if user not in self.members:
            self.members.append(user)
            return True
        return False

    def post_resource(self, resource):
        self.resources.append(resource)

    def show_resources(self):
        if not self.resources:
            print(f"  (no resources yet in {self.name})")
            return
        for resource in self.resources:
            resource.display()  # polymorphism: display() behaves differently per subclass

    def __str__(self):
        return self.name


class DepartmentCommunity(Community):
    """Open to any student in that department. Uses default join behavior."""

    def __init__(self, name, department):
        super().__init__(name)
        self.department = department


class CourseCommunity(Community):
    """Restricted to an enrolled list, overriding add_member()."""

    def __init__(self, name, course_code, enrolled_ids):
        super().__init__(name)
        self.course_code = course_code
        self.enrolled_ids = enrolled_ids  # list of school_id values allowed to join

    def add_member(self, user):
        if user.school_id not in self.enrolled_ids:
            print(f"  -> {user.name} is not enrolled in {self.course_code}.")
            return False
        if user not in self.members:
            self.members.append(user)
            return True
        return False