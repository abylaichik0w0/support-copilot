from copilot_part2 import PartTwo

p = PartTwo()
msgs = [{"role": "player", "text": "оскорбил меня и мою семью в чате, 2.1 оп"}]
print(p.run("complaint", msgs, "ru", "2.1 оп"))