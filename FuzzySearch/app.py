import sqlite3
from flask import Flask, render_template, request, jsonify

# Initialise the Flask app object
app = Flask(__name__)


# To Show index page
@app.route('/')
def my_form():
    return render_template('index.html')


# To Search the User Input Word
@app.route('/search')
def search_word():
    # Get word from form
    word = request.args.get('word')
    # variable initializations
    # To store words that match exactly with user input
    rank_list = []
    # To store words that match with user input
    match_list = []
    # Dictionary that will be appended to the match_list
    dictWord = {}
    # Counter to calculate frequency score for each word
    frequency_counter = 0
    # Counter to calculate score for each words based on size
    sbs_counter = 0

    # Function to calculate Frequency score for each word in the list
    def freqScoreCalc():
        global frequency_counter
        frequency_counter = 0

        # Connect to database
        conn = sqlite3.connect('corpus.db')
        like_word = '%'+word+'%'
        # Query to get all the words containing user input in order of its size
        sql_cmd = "select word, frequency from corpus where word like '{}' order by frequency asc".format(like_word)
        cursor = conn.execute(sql_cmd)
        for row in cursor:
            dictWord['word'] = str(row[0])
            dictWord['frequency'] = row[1]
            dictWord['sbs'] = 0
            # If user input matches with word of database
            if word == str(row[0]):
                dictWord['fs'] = 0
                # Append the word to rank_list
                rank_list.append(dictWord.copy())
            # Increment the counter for the first time
            elif frequency_counter == 0:
                frequency_counter = frequency_counter + 1
                dictWord['fs'] = frequency_counter
                match_list.append(dictWord.copy())
            # Check equality of frequencies among words
            else:
                if match_list[frequency_counter-1]['frequency'] == row[1]:
                    # Donot increment if the frequencies are same
                    dictWord['fs'] = frequency_counter
                else:
                    frequency_counter = frequency_counter + 1
                    dictWord['fs'] = frequency_counter
                # Append the dictionary to list
                match_list.append(dictWord.copy())

        conn.close()

    def shortBegScoreCalc():
        global sbs_counter
        sbs_counter = 0
        # To store length of previous and current words
        prevStrLen = 0
        curStrLen = 0

        # Connect to the database
        conn = sqlite3.connect('corpus.db')
        like_word = '%'+word+'%'
        start_with = word+'%'
        # Create View that stores words having user input
        sql_cmd = "CREATE TEMP VIEW IF NOT EXISTS DescWords AS select * from corpus where word like '{}' order by length(word) desc".format(like_word)
        cursor = conn.execute(sql_cmd)

        # Create View that stores words that short and start with user input
        sql_cmd = "CREATE TEMP VIEW IF NOT EXISTS ShortBegDsc AS select * from corpus where word like '{}' order by length(word) desc".format(start_with)
        cursor = conn.execute(sql_cmd)

        # Create View that stores words not present in view ShortBegDsc
        sql_cmd = "Select * from DescWords where word NOT IN (Select word from ShortBegDsc)"
        cursor = conn.execute(sql_cmd)
        for row in cursor:
            dbword = str(row[0])
            # If the user inout matches with database neglect it
            if dbword == word:
                continue
            # When the counter is zero
            elif sbs_counter == 0:
                for match in match_list:
                    if match['word'] == dbword:
                        # Increment when the word in list matches with db
                        sbs_counter = sbs_counter + 1
                        match['sbs'] = sbs_counter
                        # Calculate Length of string
                        prevStrLen = len(dbword)
                        curStrLen = len(dbword)
                        # When the counter is not zero
                    else:
                        for match in match_list:
                            if match['word'] == dbword:
                                curStrLen = len(match['word'])
                                # Dont increment if words have same length
                                if prevStrLen == curStrLen:
                                    match['sbs'] = sbs_counter
                                else:
                                    sbs_counter = sbs_counter + 1
                                    match['sbs'] = sbs_counter
                                    prevStrLen = curStrLen

        # Query to select all the rows from the view
        sql_cmd = "Select * from ShortBegDsc"
        cursor = conn.execute(sql_cmd)
        for row in cursor:
            dbword = str(row[0])
            # If the user inout matches with database neglect it
            if dbword == word:
                continue
            else:
                for match in match_list:
                    if match['word'] == dbword:
                        curStrLen = len(match['word'])
                        # Dont increment if words have same length
                        if prevStrLen == curStrLen:
                            match['sbs'] = sbs_counter
                        else:
                            sbs_counter = sbs_counter + 1
                            match['sbs'] = sbs_counter
                            prevStrLen = curStrLen        
        
        # Close the connection
        conn.close()

    # To calculate Frequency Score of Each Word in the match_list
    freqScoreCalc()
    # To calculate Score based on size and position of user input in word
    shortBegScoreCalc()

    # List with items in sorted order based on calculated scores
    final_list = rank_list + sorted(
        match_list, key=lambda k: k['fs']+k['sbs'], reverse=True)
    # Stores only words to be shown to the user
    newFinalList = []
    for list_item in final_list:
        newFinalList.append(list_item['word'])

    # To empty the lists
    rank_list[:] = []
    match_list[:] = []

    # To output the JSON array of 25 words
    return jsonify(newFinalList[0:25])


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
