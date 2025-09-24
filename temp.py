def isPalindrome(tString):
    if len(tString) <= 1:
        return True
    if not isPalindrome(tString[1:len(tString)-1]):
        return False
    if tString[0] != tString[len(tString)-1]:
        return False
    return True

print(isPalindrome('level'))