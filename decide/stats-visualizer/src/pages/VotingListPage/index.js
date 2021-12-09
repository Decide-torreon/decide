import React, { useState, useEffect } from 'react';
import { Card, CardContent, Typography, Grid } from '@mui/material';
import { Link } from 'react-router-dom';

import VotingService from 'domain/service/locator/voting';
import ChartService from 'domain/service/locator/chart';
import { VOTING_STATES } from 'domain/model/voting-state.model';
import PageTitle from 'components/PageTitle';
import DoughnutChart from 'components/DoughnutChart';

import pageStyle from './style.module.scss';

const VOTING_STATES_VALUES = Object.values(VOTING_STATES);

export default function VotingListPage() {

  const [ votings, setVotings ]  = useState([]);
  const [ votingsByStateDataset, setVotingsByStateDataset ]  = useState(null);

  useEffect(() => {
    VotingService.findAll()
      .then(votings => setVotings(votings))
      .catch(err => console.error('error getting votings', err));

    ChartService.countVotingsGroupedByState()
      .then((votingsByState) => {
        const states = VOTING_STATES_VALUES
          .sort((state1, state2) => state1.name > state2.name ? 1 : -1);
        
        const data = {
          labels: states.map(state => state.name),
          datasets: [{
            label: 'Votings count by state',
            data: states.map(state => votingsByState[state.code] || 0)
          }]
        }

        console.log('doughnut chart data', data);
        setVotingsByStateDataset(data);
      })
      .catch(err => console.error('error getting votings by state', err));
  }, [])


  return (<>
    <PageTitle
      style={{ marginTop: '1rem' }}
    >Voting list page</PageTitle>

    <Grid container spacing={2}>
      <Grid item xs={12} md={6}>
        { votings.map((voting, i) => (
            <Card key={ i } className={pageStyle.votingItem}>
              <CardContent>
                <Link to={ `/voting/${voting.id}` }>
                  <Typography sx={{ fontSize: 16 }} color="text.primary" gutterBottom>
                  { voting.name }
                  </Typography>
                  { voting.state.name }
                </Link>
              </CardContent>
            </Card>
          ))
        }
      </Grid>
      <Grid item xs={12} md={6}>
        { votingsByStateDataset != null && (
          <Card>
            <CardContent>
              <DoughnutChart {...votingsByStateDataset} />
            </CardContent>
          </Card>
        )}
      </Grid>
    </Grid>    
  </>);
}