import React, { useState, useEffect } from 'react';
import VotingService from 'domain/service/locator/voting';


export default function VotingListPage() {

  const [ votings, setVotings ]  = useState([]);

  useEffect(() => {
    VotingService.findAll()
      .then(votings => setVotings(votings))
      .catch(err => console.error('error getting votings', err));
  }, [])


  return (<>
    <h4>Voting list page</h4>

    <ul>
      { votings.map((voting, i) => (
          <li key={ i }>{ voting.name }</li>
        ))
      }

    </ul>
    </>
  );
}