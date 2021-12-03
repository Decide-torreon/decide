import Http from '../http/http';
import Voting from 'domain/model/voting.model';

window.Voting = Voting;

export default class VotingRepository {

    async listVotings() {
        const votings = await Http.get('http://localhost:8000/voting/');

        console.log('votings', votings);
        // TODO map votings to VotingModel
        return votings instanceof Array
          ? (votings.map(voting => new Voting(voting)))
          : [];
    }

    async getVoting(id) {
        const voting = await Http.get(`http://localhost:8000/voting/?id=${id}`);
        // TODO map votings to VotingModel
        return voting;
    }

}