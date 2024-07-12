

def compare_lists(old_list, new_list):

    new_members = new_list
    deleted_members = []
    same_members = []

    for old_member in old_list:
        if old_member in new_list:
            same_members.append(old_member)
            new_members.remove(old_member)
        else:
            deleted_members.append(old_member)

    return new_members, same_members, deleted_members

def compare_lists2(old_list, new_list):

    new_members = []
    deleted_members = old_list
    same_members = []

    for new_member in new_list:
        if new_member in old_list:
            same_members.append(new_member)
            deleted_members.remove(new_member)
        else:
            new_members.append(new_member)

    return new_members, same_members, deleted_members

