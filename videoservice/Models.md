Model planning for membership platform

Membership
    - slug
    - type (free, pro, entreprise)
    - price
    - stripe plan id

UserMembership
    - user              (fk to user)
    - stripe customer id
    - membership type   (fk to membership)

Subscription (when user pay membership)
    - user membership
    - stripe subscription id (fk to usermembership)
    - active 

Course
    - slug
    - title
    - description
    - allowed memberships (fk to membership)

Lesson
    - slug
    - title
    - course (fk to course)
    - position